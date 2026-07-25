#!/usr/bin/env python3
"""Unified CLI for the personal agent vault (any coding agent).

Subcommands:
  init | status | keys | remember | capture | path | context | preview
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_vault import (  # noqa: E402
    brief_context_for_agent,
    resolve_vault_path,
    secrets_file,
)


SCRIPTS = Path(__file__).resolve().parent


def _run(script: str, extra: list[str] | None = None) -> int:
    cmd = [sys.executable, str(SCRIPTS / script)]
    if extra:
        cmd.extend(extra)
    return subprocess.call(cmd)


def cmd_remember(args: argparse.Namespace) -> int:
    import auto_capture  # local

    vault = resolve_vault_path(args.vault)
    if not vault.is_dir():
        _run("ensure_vault.py", ["--vault", str(vault)])
    text = args.text or " ".join(args.words or [])
    if not text.strip():
        print("Usage: vault_cli.py remember <text>", file=sys.stderr)
        return 2
    kind = (args.kind or "auto").lower()
    if kind == "reminder":
        ok = auto_capture.append_reminder(vault, text.strip())
        print("Reminder saved." if ok else "Reminder already present.")
        return 0
    if kind == "secret":
        # treat whole text as a secret blob scan
        result = auto_capture.process_text(text, vault, source="remember")
        if result["secrets_added"]:
            masks = ", ".join(s["masked"] for s in result["secrets_added"])
            print(f"Secret saved (masked): {masks}")
        else:
            # force store as generic secret row
            path = secrets_file(vault)
            label = args.label or "manual"
            if auto_capture.append_secret(path, "manual", label, text.strip(), "remember"):
                print(f"Secret saved as label={label} value={auto_capture.mask_secret(text.strip())}")
            else:
                print("Secret already present (deduped).")
        return 0
    # auto or fact
    result = auto_capture.process_text(text, vault, source="remember")
    if result["secrets_added"] or result["personal_added"]:
        if result["secrets_added"]:
            masks = ", ".join(s["masked"] for s in result["secrets_added"])
            print(f"Captured secrets: {masks}")
        if result["personal_added"]:
            bits = ", ".join(f"{p['kind']}:{p['value']}" for p in result["personal_added"])
            print(f"Captured personal: {bits}")
        return 0
    # force as about-me note
    ok = auto_capture.append_personal(vault / "me" / "about-me.md", "note", text.strip())
    print("Fact saved to about-me." if ok else "Already present.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Personal agent vault CLI")
    parser.add_argument("--vault", help="Override vault path")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Create / repair vault")
    sub.add_parser("status", help="Dashboard (no secret values)")
    sub.add_parser("keys", help="List key labels only")
    sub.add_parser("path", help="Print vault path")
    sub.add_parser("context", help="Print non-secret brief for agents")
    p_prev = sub.add_parser("preview", help="Start local HTTP preview")
    p_prev.add_argument("--port", type=int, default=8765)
    p_prev.add_argument("--open", action="store_true")

    p_cap = sub.add_parser("capture", help="Scan text/file/stdin for auto-capture")
    p_cap.add_argument("--text")
    p_cap.add_argument("--file")
    p_cap.add_argument("--json", action="store_true")

    p_rem = sub.add_parser("remember", help="Save a fact, reminder, or secret")
    p_rem.add_argument("words", nargs="*", help="Text to remember")
    p_rem.add_argument("--text", help="Text to remember")
    p_rem.add_argument(
        "--kind",
        choices=["auto", "fact", "reminder", "secret"],
        default="auto",
    )
    p_rem.add_argument("--label", help="Label when --kind secret")

    args = parser.parse_args()
    vault = resolve_vault_path(args.vault)
    extra_vault = ["--vault", str(vault)] if args.vault else []

    if args.cmd == "init":
        return _run("ensure_vault.py", extra_vault)
    if args.cmd == "status":
        return _run("vault_status.py", extra_vault)
    if args.cmd == "keys":
        return _run("vault_keys.py", extra_vault)
    if args.cmd == "path":
        print(vault)
        return 0
    if args.cmd == "context":
        if not vault.is_dir():
            _run("ensure_vault.py", ["--vault", str(vault)])
        print(brief_context_for_agent(vault))
        return 0
    if args.cmd == "preview":
        extra = extra_vault + ["--port", str(args.port)]
        if args.open:
            extra.append("--open")
        return _run("preview_server.py", extra)
    if args.cmd == "capture":
        extra = list(extra_vault)
        if args.text:
            extra += ["--text", args.text]
        if args.file:
            extra += ["--file", args.file]
        if args.json:
            extra.append("--json")
        else:
            extra.append("--verbose")
        extra += ["--source", "cli"]
        return _run("quiet_watcher.py", extra)
    if args.cmd == "remember":
        return cmd_remember(args)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
