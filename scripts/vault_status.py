#!/usr/bin/env python3
"""Print a compact vault dashboard (no secret values)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_vault import (  # noqa: E402
    count_open_todos,
    count_secret_rows,
    resolve_vault_path,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Vault status dashboard")
    parser.add_argument("--vault", help="Override vault path")
    args = parser.parse_args()

    vault = resolve_vault_path(args.vault)
    if not vault.is_dir():
        print(f"Vault missing: {vault}")
        print("Run ensure_vault.py or /vault-init first.")
        return 1

    open_todos = count_open_todos(vault)
    secret_n = count_secret_rows(vault)
    about = vault / "me" / "about-me.md"
    about_preview = ""
    if about.is_file():
        lines = [
            ln.strip()
            for ln in about.read_text(encoding="utf-8", errors="replace").splitlines()
            if ln.strip() and not ln.strip().startswith("#") and not ln.strip().startswith("(")
        ]
        about_preview = "; ".join(lines[:3])[:200]

    print("=== Grok Build Vault ===")
    print(f"Path:          {vault}")
    print(f"Open todos:    {open_todos}")
    print(f"Secret rows:   {secret_n} (values hidden)")
    if about_preview:
        print(f"About preview: {about_preview}")
    print("Top-level:")
    for child in sorted(vault.iterdir(), key=lambda p: p.name.lower()):
        kind = "dir " if child.is_dir() else "file"
        print(f"  [{kind}] {child.name}")
    print("Commands: /vault-todo  /vault-remember  /vault-preview")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
