#!/usr/bin/env python3
"""Create or refresh the local personal vault from the plugin template (idempotent)."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_vault import (  # noqa: E402
    ensure_private_dir,
    load_config,
    migrate_secrets_to_deep,
    protect_path,
    resolve_vault_path,
    save_config,
    secrets_file,
    template_dir,
)


def _is_effectively_empty(path: Path) -> bool:
    if not path.is_file():
        return True
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    return len(text) == 0


def copy_template_tree(src: Path, dest: Path) -> list[str]:
    """Copy missing files only; never overwrite non-empty existing files."""
    created: list[str] = []
    for root, dirs, files in os.walk(src):
        rel_root = Path(root).relative_to(src)
        dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git"}]
        target_dir = dest / rel_root
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in files:
            if name.endswith(".pyc"):
                continue
            s = Path(root) / name
            d = dest / rel_root / name
            if d.exists() and d.is_file() and not _is_effectively_empty(d):
                continue
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, d)
            created.append(str(d))
    return created


def ensure_secrets_file(vault: Path) -> Path:
    ensure_private_dir(vault)
    migrate_secrets_to_deep(vault)
    secrets = secrets_file(vault)
    # Force deep path if nothing exists yet
    if not secrets.is_file():
        secrets = vault / "me" / ".private" / "secrets.local.md"
    if secrets.exists():
        protect_path(secrets)
        return secrets

    example = vault / "me" / "secrets.local.md.example"
    header = (
        "# Local secrets (DO NOT COMMIT)\n\n"
        "Deep path: `me/.private/secrets.local.md` — gitignored, restricted.\n"
        "Values are **plaintext on disk**. Prefer full-disk encryption.\n"
        "This is convenience capture, not a password manager.\n\n"
        "## Entries\n\n"
        "| When (UTC) | Kind | Label | Value | Source |\n"
        "|------------|------|-------|-------|--------|\n"
    )
    if example.is_file():
        text = example.read_text(encoding="utf-8")
        lines = []
        for line in text.splitlines():
            if "«redacted" in line or "example" in line.lower() and line.strip().startswith("|"):
                # drop example data rows only
                if "template" in line.lower() or "example" in line.lower():
                    continue
            lines.append(line)
        body = "\n".join(lines).rstrip() + "\n"
        # ensure we don't leave only a broken table — rewrite clean if needed
        if "| When (UTC)" not in body:
            body = header
        secrets.parent.mkdir(parents=True, exist_ok=True)
        secrets.write_text(body if "| When (UTC)" in body else header, encoding="utf-8")
    else:
        secrets.parent.mkdir(parents=True, exist_ok=True)
        secrets.write_text(header, encoding="utf-8")
    protect_path(secrets.parent)
    protect_path(secrets)
    return secrets


def main() -> int:
    parser = argparse.ArgumentParser(description="Ensure personal agent vault exists")
    parser.add_argument("--vault", help="Override vault path")
    args = parser.parse_args()

    vault = resolve_vault_path(args.vault)
    tmpl = template_dir()
    vault.mkdir(parents=True, exist_ok=True)
    copy_template_tree(tmpl, vault)
    ensure_private_dir(vault)
    ensure_secrets_file(vault)

    cfg = load_config()
    cfg["vault_path"] = str(vault)
    cfg["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if "created_at" not in cfg:
        cfg["created_at"] = cfg["updated_at"]
    cfg["secrets_path"] = str(secrets_file(vault))
    save_config(cfg)

    print(f"Vault ready: {vault}")
    print(f"Secrets: {secrets_file(vault)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
