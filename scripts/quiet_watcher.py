#!/usr/bin/env python3
"""Quiet vault watcher — local "subagent" that runs after every prompt.

Not an LLM spawn. Deterministic, fail-open, stdlib-only:
  1. ensure vault exists
  2. scan text for secrets + durable personal facts
  3. write deep protected storage
  4. append activity log (masked; never secret values)
  5. stay silent unless --verbose / --json

Grok hooks and Hermes pre_llm_call both call this path.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import auto_capture  # noqa: E402
from lib_vault import (  # noqa: E402
    append_activity,
    resolve_vault_path,
)


def watch(text: str, vault: Path, source: str) -> dict:
    if not text.strip():
        return {"ok": True, "skipped": "empty", "vault": str(vault)}

    # Ensure vault soft
    if not vault.is_dir():
        ensure = Path(__file__).with_name("ensure_vault.py")
        if ensure.is_file():
            import subprocess

            subprocess.run(
                [sys.executable, str(ensure), "--vault", str(vault)],
                check=False,
                capture_output=True,
                timeout=45,
            )
        vault = resolve_vault_path(str(vault))

    if not vault.is_dir():
        return {"ok": False, "error": "vault_missing", "path": str(vault)}

    result = auto_capture.process_text(text, vault, source=source)
    secrets_n = len(result.get("secrets_added") or [])
    personal_n = len(result.get("personal_added") or [])

    if secrets_n or personal_n:
        bits = []
        if secrets_n:
            masks = ", ".join(
                f"{s['kind']}={s['masked']}" for s in result["secrets_added"]
            )
            bits.append(f"sealed:{masks}")
            append_activity(vault, "secret", f"sealed {secrets_n} · {masks}")
        if personal_n:
            facts = ", ".join(
                f"{p['kind']}:{p['value']}" for p in result["personal_added"]
            )
            bits.append(f"facts:{facts}")
            append_activity(vault, "fact", facts[:140])
        summary = "; ".join(bits)
    else:
        summary = "noop"
        # still touch a light heartbeat only if explicitly requested — skip to avoid noise

    return {
        "ok": True,
        "vault": str(vault),
        "secrets_added": result.get("secrets_added") or [],
        "personal_added": result.get("personal_added") or [],
        "summary": summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Quiet agent-vault watcher")
    parser.add_argument("--vault")
    parser.add_argument("--text")
    parser.add_argument("--file")
    parser.add_argument("--source", default="watcher")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    vault = resolve_vault_path(args.vault)
    text = args.text or ""
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8", errors="replace")
    if not text and not sys.stdin.isatty():
        raw = sys.stdin.read()
        if raw.strip():
            try:
                payload = json.loads(raw)
                text = (
                    auto_capture.extract_text_from_hook(payload)
                    if isinstance(payload, dict)
                    else raw
                )
                if not text.strip() and isinstance(payload, dict):
                    text = json.dumps(payload)
            except json.JSONDecodeError:
                text = raw

    try:
        out = watch(text, vault, args.source)
    except Exception as exc:  # fail-open for hooks
        out = {"ok": False, "error": str(exc)}
        if args.json:
            print(json.dumps(out))
        return 0

    if args.json:
        print(json.dumps(out))
    elif args.verbose:
        if out.get("skipped"):
            print("watcher: skipped empty")
        elif out.get("summary") == "noop":
            print("watcher: nothing new")
        else:
            print(f"watcher: {out.get('summary')}")
    # default quiet: print nothing
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
