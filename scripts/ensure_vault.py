#!/usr/bin/env python3
"""Create or refresh the local Grok Build vault from the plugin template (idempotent)."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running as script
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_vault import (  # noqa: E402
    load_config,
    resolve_vault_path,
    save_config,
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
        # skip Python cache etc.
        dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git"}]
        target_dir = dest / rel_root
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in files:
            if name.endswith(".pyc"):
                continue
            s = Path(root) / name
            # secrets.local.md.example is template-only; runtime secrets created separately
            d = dest / rel_root / name
            if d.exists():
                if d.is_file() and not _is_effectively_empty(d):
                    continue
                if d.is_file() and _is_effectively_empty(d):
                    # empty placeholder — still don't overwrite if user cleared intentionally? allow fill from template
                    pass
                else:
                    continue
            d.parent.mkdir(parents=True, exist_ok=True)
            if not d.exists() or _is_effectively_empty(d):
                if d.exists() and not _is_effectively_empty(d):
                    continue
                if d.exists() and _is_effectively_empty(d):
                    # only fill truly empty files from template once
                    shutil.copy2(s, d)
                    created.append(str(d))
                else:
                    shutil.copy2(s, d)
                    created.append(str(d))
    return created


def ensure_secrets_file(vault: Path) -> None:
    secrets = vault / "me" / "secrets.local.md"
    example = vault / "me" / "secrets.local.md.example"
    if secrets.exists():
        return
    if example.is_file():
        text = example.read_text(encoding="utf-8")
        # strip example row so user starts clean
        lines = []
        for line in text.splitlines():
            if "sk-example-not-real" in line:
                continue
            lines.append(line)
        secrets.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    else:
        secrets.write_text(
            "# Local secrets (DO NOT COMMIT)\n\n"
            "## Entries\n\n"
            "| When (UTC) | Kind | Label | Value | Source |\n"
            "|------------|------|-------|-------|--------|\n",
            encoding="utf-8",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Ensure Grok Build vault exists")
    parser.add_argument("--vault", help="Override vault path")
    args = parser.parse_args()

    vault = resolve_vault_path(args.vault)
    tmpl = template_dir()
    vault.mkdir(parents=True, exist_ok=True)
    copy_template_tree(tmpl, vault)
    ensure_secrets_file(vault)

    cfg = load_config()
    cfg["vault_path"] = str(vault)
    cfg["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if "created_at" not in cfg:
        cfg["created_at"] = cfg["updated_at"]
    save_config(cfg)

    print(f"Vault ready: {vault}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
