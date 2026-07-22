#!/usr/bin/env python3
"""Heuristic auto-capture of secrets and light personal facts into the vault.

Reads hook JSON from stdin (Grok hooks) or --text / --file.
Never prints full secret values; masks them in the summary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_vault import resolve_vault_path  # noqa: E402

# --- secret patterns (value group when possible) ---
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("api_key", re.compile(r"\b(sk-[A-Za-z0-9_\-]{16,})\b")),
    ("api_key", re.compile(r"\b(sk-or-[A-Za-z0-9_\-]{16,})\b")),
    ("api_key", re.compile(r"\b(xai-[A-Za-z0-9_\-]{16,})\b")),
    ("github_token", re.compile(r"\b(ghp_[A-Za-z0-9]{20,})\b")),
    ("github_token", re.compile(r"\b(github_pat_[A-Za-z0-9_]{20,})\b")),
    ("aws_key", re.compile(r"\b(AKIA[0-9A-Z]{16})\b")),
    ("bearer", re.compile(r"\bBearer\s+([A-Za-z0-9\-._~+/]+=*)", re.I)),
    ("jwt", re.compile(r"\b(eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+)\b")),
    ("password", re.compile(r"(?i)\bpassword\s*[:=]\s*([^\s,;\"']{6,})")),
    ("token", re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|secret[_-]?key)\s*[:=]\s*([^\s,;\"']{8,})")),
    ("connection", re.compile(r"\b((?:postgres|mysql|mongodb(?:\+srv)?|redis)://[^\s\"']+)\b", re.I)),
]

PERSONAL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("name", re.compile(r"(?i)\bmy name is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})")),
    ("name", re.compile(r"(?i)\bi am\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b")),
    ("preference", re.compile(r"(?i)\bi prefer\s+(.{5,80}?)(?:\.|$)")),
    ("work", re.compile(r"(?i)\bi work(?:\s+at|\s+on|\s+as)\s+(.{3,80}?)(?:\.|$)")),
    ("timezone", re.compile(r"(?i)\b(?:timezone|time zone)\s*(?:is|:)?\s*([A-Za-z_/+-]{3,40})")),
    ("email", re.compile(r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")),
]


def mask_secret(value: str) -> str:
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}…****"


def value_fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def extract_text_from_hook(payload: dict) -> str:
    chunks: list[str] = []
    for key in ("prompt", "userPrompt", "text", "message", "content"):
        val = payload.get(key)
        if isinstance(val, str):
            chunks.append(val)
    # nested common shapes
    for key in ("toolInput", "input", "body"):
        val = payload.get(key)
        if isinstance(val, dict):
            chunks.append(extract_text_from_hook(val))
        elif isinstance(val, str):
            chunks.append(val)
    if "messages" in payload and isinstance(payload["messages"], list):
        for m in payload["messages"]:
            if isinstance(m, dict):
                c = m.get("content") or m.get("text")
                if isinstance(c, str):
                    chunks.append(c)
    return "\n".join(chunks)


def find_secrets(text: str) -> list[tuple[str, str, str]]:
    found: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for kind, pat in SECRET_PATTERNS:
        for m in pat.finditer(text):
            val = m.group(1) if m.lastindex else m.group(0)
            val = val.strip().strip("\"'")
            if len(val) < 6:
                continue
            fp = value_fingerprint(val)
            if fp in seen:
                continue
            seen.add(fp)
            label = kind
            found.append((kind, label, val))
    return found


def find_personal(text: str) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    seen: set[str] = set()
    for kind, pat in PERSONAL_PATTERNS:
        for m in pat.finditer(text):
            val = m.group(1).strip().rstrip(".")
            key = f"{kind}:{val.lower()}"
            if key in seen:
                continue
            seen.add(key)
            items.append((kind, val))
    return items


def ensure_secrets_table(path: Path) -> None:
    if path.is_file():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Local secrets (DO NOT COMMIT)\n\n"
        "## Entries\n\n"
        "| When (UTC) | Kind | Label | Value | Source |\n"
        "|------------|------|-------|-------|--------|\n",
        encoding="utf-8",
    )


def secret_already_present(path: Path, value: str) -> bool:
    if not path.is_file():
        return False
    body = path.read_text(encoding="utf-8", errors="replace")
    return value in body


def append_secret(path: Path, kind: str, label: str, value: str, source: str) -> bool:
    ensure_secrets_table(path)
    if secret_already_present(path, value):
        return False
    when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # escape pipes in value for markdown table
    safe = value.replace("|", "\\|")
    row = f"| {when} | {kind} | {label} | {safe} | {source} |\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(row)
    return True


def append_personal(about_path: Path, kind: str, value: str) -> bool:
    about_path.parent.mkdir(parents=True, exist_ok=True)
    if not about_path.is_file():
        about_path.write_text(
            "# About Me\n\n## Identity\n\n## Preferences\n\n## Constraints\n\n## Notes\n\n",
            encoding="utf-8",
        )
    body = about_path.read_text(encoding="utf-8", errors="replace")
    bullet = f"- {value}"
    if value.lower() in body.lower():
        return False
    section_map = {
        "name": "## Identity",
        "email": "## Identity",
        "work": "## Identity",
        "timezone": "## Identity",
        "preference": "## Preferences",
    }
    heading = section_map.get(kind, "## Notes")
    if heading not in body:
        body = body.rstrip() + f"\n\n{heading}\n\n"
    # insert bullet after heading
    parts = body.split(heading, 1)
    if len(parts) != 2:
        body = body.rstrip() + f"\n\n{heading}\n\n{bullet}\n"
    else:
        rest = parts[1]
        # skip blank lines after heading
        body = parts[0] + heading + "\n\n" + bullet + "\n" + rest.lstrip("\n")
    about_path.write_text(body, encoding="utf-8")
    return True


def process_text(text: str, vault: Path, source: str) -> dict:
    secrets_path = vault / "me" / "secrets.local.md"
    about_path = vault / "me" / "about-me.md"
    secrets_added = []
    personal_added = []

    for kind, label, value in find_secrets(text):
        if append_secret(secrets_path, kind, label, value, source):
            secrets_added.append({"kind": kind, "masked": mask_secret(value)})

    for kind, value in find_personal(text):
        if append_personal(about_path, kind, value):
            personal_added.append({"kind": kind, "value": value[:80]})

    return {
        "vault": str(vault),
        "secrets_added": secrets_added,
        "personal_added": personal_added,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-capture secrets and personal facts")
    parser.add_argument("--vault", help="Override vault path")
    parser.add_argument("--text", help="Text to scan")
    parser.add_argument("--file", help="File to scan")
    parser.add_argument("--source", default="hook", help="Source label")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    args = parser.parse_args()

    vault = resolve_vault_path(args.vault)
    # If vault missing, soft no-op so hooks never break sessions
    if not vault.is_dir():
        # try ensure via sibling script
        ensure = Path(__file__).with_name("ensure_vault.py")
        if ensure.is_file():
            import subprocess

            subprocess.run([sys.executable, str(ensure), "--vault", str(vault)], check=False)
        vault = resolve_vault_path(args.vault)

    text = args.text or ""
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8", errors="replace")
    if not text and not sys.stdin.isatty():
        raw = sys.stdin.read()
        if raw.strip():
            try:
                payload = json.loads(raw)
                text = extract_text_from_hook(payload) if isinstance(payload, dict) else raw
                # include raw string fields if extract empty
                if not text.strip() and isinstance(payload, dict):
                    text = json.dumps(payload)
            except json.JSONDecodeError:
                text = raw

    if not text.strip():
        # empty prompt — success no-op for hooks
        if args.json:
            print(json.dumps({"ok": True, "skipped": "empty"}))
        return 0

    if not vault.is_dir():
        if args.json:
            print(json.dumps({"ok": False, "error": "vault_missing", "path": str(vault)}))
        else:
            print(f"Vault missing: {vault}", file=sys.stderr)
        return 0  # fail-open for hooks

    result = process_text(text, vault, args.source)
    if args.json:
        print(json.dumps({"ok": True, **result}))
    else:
        if result["secrets_added"]:
            masks = ", ".join(f"{s['kind']}={s['masked']}" for s in result["secrets_added"])
            print(f"Captured secrets: {masks}")
        if result["personal_added"]:
            bits = ", ".join(f"{p['kind']}:{p['value']}" for p in result["personal_added"])
            print(f"Captured personal: {bits}")
        if not result["secrets_added"] and not result["personal_added"]:
            print("No new captures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
