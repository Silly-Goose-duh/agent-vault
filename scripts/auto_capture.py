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
from lib_vault import (  # noqa: E402
    ensure_private_dir,
    protect_path,
    resolve_vault_path,
    secrets_file,
)

# --- secret patterns (value group when possible) ---
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("api_key", re.compile(r"\b(sk-[A-Za-z0-9_\-]{16,})\b")),
    ("api_key", re.compile(r"\b(sk-or-[A-Za-z0-9_\-]{16,})\b")),
    ("api_key", re.compile(r"\b(xai-[A-Za-z0-9_\-]{16,})\b")),
    ("github_token", re.compile(r"\b(ghp_[A-Za-z0-9]{20,})\b")),
    ("github_token", re.compile(r"\b(gho_[A-Za-z0-9]{20,})\b")),
    ("github_token", re.compile(r"\b(github_pat_[A-Za-z0-9_]{20,})\b")),
    ("aws_key", re.compile(r"\b(AKIA[0-9A-Z]{16})\b")),
    ("bearer", re.compile(r"\bBearer\s+([A-Za-z0-9\-._~+/]+=*)", re.I)),
    ("jwt", re.compile(r"\b(eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+)\b")),
    ("password", re.compile(r"(?i)\bpassword\s*[:=]\s*([^\s,;\"']{6,})")),
    (
        "token",
        re.compile(
            r"(?i)\b(?:api[_-]?key|access[_-]?token|secret[_-]?key|service[_-]?role)\s*[:=]\s*([^\s,;\"']{8,})"
        ),
    ),
    (
        "connection",
        re.compile(r"\b((?:postgres|mysql|mongodb(?:\+srv)?|redis)://[^\s\"']+)\b", re.I),
    ),
    ("supabase_ref", re.compile(r"\b(sbp_[A-Za-z0-9]{20,})\b")),
]

PERSONAL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("name", re.compile(r"(?i)\bmy name is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})")),
    ("name", re.compile(r"(?i)\bi am\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b")),
    ("name", re.compile(r"(?i)\bcall me\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b")),
    ("preference", re.compile(r"(?i)\bi prefer\s+(.{5,80}?)(?:\.|$)")),
    ("preference", re.compile(r"(?i)\balways\s+(.{5,80}?)(?:\.|$)")),
    ("work", re.compile(r"(?i)\bi work(?:\s+at|\s+on|\s+as)\s+(.{3,80}?)(?:\.|$)")),
    ("timezone", re.compile(r"(?i)\b(?:timezone|time zone)\s*(?:is|:)?\s*([A-Za-z_/+-]{3,40})")),
    ("email", re.compile(r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")),
    ("phone", re.compile(r"(?i)\b(?:my )?(?:phone|mobile)\s*(?:is|:)?\s*(\+?[\d][\d\s\-()]{7,})")),
]


def mask_secret(value: str) -> str:
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}…****"


def value_fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def extract_text_from_hook(payload: dict) -> str:
    chunks: list[str] = []
    for key in (
        "prompt",
        "userPrompt",
        "user_message",
        "text",
        "message",
        "content",
        "original_user_message",
    ):
        val = payload.get(key)
        if isinstance(val, str):
            chunks.append(val)
    for key in ("toolInput", "input", "body"):
        val = payload.get(key)
        if isinstance(val, dict):
            chunks.append(extract_text_from_hook(val))
        elif isinstance(val, str):
            chunks.append(val)
    if "messages" in payload and isinstance(payload["messages"], list):
        for m in payload["messages"]:
            if isinstance(m, dict):
                role = (m.get("role") or "").lower()
                if role and role not in ("user", "human", ""):
                    continue
                c = m.get("content") or m.get("text")
                if isinstance(c, str):
                    chunks.append(c)
                elif isinstance(c, list):
                    for part in c:
                        if isinstance(part, dict) and isinstance(part.get("text"), str):
                            chunks.append(part["text"])
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
            # skip obvious placeholders
            low = val.lower()
            if any(x in low for x in ("example", "redacted", "xxxx", "your_", "placeholder")):
                continue
            fp = value_fingerprint(val)
            if fp in seen:
                continue
            seen.add(fp)
            found.append((kind, kind, val))
    return found


def find_personal(text: str) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    seen: set[str] = set()
    for kind, pat in PERSONAL_PATTERNS:
        for m in pat.finditer(text):
            val = m.group(1).strip().rstrip(".")
            # filter false positives like "I am going" / "I am not"
            if kind == "name":
                if val.lower() in {
                    "going",
                    "not",
                    "just",
                    "trying",
                    "using",
                    "working",
                    "here",
                    "fine",
                    "ready",
                    "done",
                    "back",
                }:
                    continue
            key = f"{kind}:{val.lower()}"
            if key in seen:
                continue
            seen.add(key)
            items.append((kind, val))
    return items


def ensure_secrets_table(path: Path) -> None:
    if path.is_file():
        protect_path(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Local secrets (DO NOT COMMIT)\n\n"
        "Stored under `me/.private/` — gitignored, owner-restricted when possible.\n"
        "Plaintext on disk. Prefer full-disk encryption. Not a password manager.\n\n"
        "## Entries\n\n"
        "| When (UTC) | Kind | Label | Value | Source |\n"
        "|------------|------|-------|-------|--------|\n",
        encoding="utf-8",
    )
    protect_path(path.parent)
    protect_path(path)


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
    safe = value.replace("|", "\\|")
    row = f"| {when} | {kind} | {label} | {safe} | {source} |\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(row)
    protect_path(path)
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
        "phone": "## Identity",
        "preference": "## Preferences",
    }
    heading = section_map.get(kind, "## Notes")
    if heading not in body:
        body = body.rstrip() + f"\n\n{heading}\n\n"
    parts = body.split(heading, 1)
    if len(parts) != 2:
        body = body.rstrip() + f"\n\n{heading}\n\n{bullet}\n"
    else:
        rest = parts[1]
        body = parts[0] + heading + "\n\n" + bullet + "\n" + rest.lstrip("\n")
    about_path.write_text(body, encoding="utf-8")
    return True


def append_reminder(vault: Path, text: str) -> bool:
    path = vault / "me" / "reminders.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.is_file():
        path.write_text(
            "# Reminders\n\n## Active\n\n## Done\n\n",
            encoding="utf-8",
        )
    body = path.read_text(encoding="utf-8", errors="replace")
    if text.lower() in body.lower():
        return False
    bullet = f"- [ ] {text}"
    if "## Active" in body:
        parts = body.split("## Active", 1)
        rest = parts[1]
        body = parts[0] + "## Active\n\n" + bullet + "\n" + rest.lstrip("\n")
    else:
        body = body.rstrip() + f"\n\n## Active\n\n{bullet}\n"
    path.write_text(body, encoding="utf-8")
    return True


def process_text(text: str, vault: Path, source: str) -> dict:
    ensure_private_dir(vault)
    secrets_path = secrets_file(vault)
    # If deep doesn't exist yet but we're writing, force deep path
    if not secrets_path.is_file():
        secrets_path = vault / "me" / ".private" / "secrets.local.md"
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
        "secrets_path": str(secrets_path),
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
    if not vault.is_dir():
        ensure = Path(__file__).with_name("ensure_vault.py")
        if ensure.is_file():
            import subprocess

            subprocess.run(
                [sys.executable, str(ensure), "--vault", str(vault)],
                check=False,
            )
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
                if not text.strip() and isinstance(payload, dict):
                    text = json.dumps(payload)
            except json.JSONDecodeError:
                text = raw

    if not text.strip():
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
