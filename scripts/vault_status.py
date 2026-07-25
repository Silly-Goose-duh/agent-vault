#!/usr/bin/env python3
"""Creative /vault dashboard — never prints secret values."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_vault import render_creative_dashboard, resolve_vault_path  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent Vault creative dashboard")
    parser.add_argument("--vault", help="Override vault path")
    parser.add_argument(
        "--no-github",
        action="store_true",
        help="Skip GitHub highlight section",
    )
    args = parser.parse_args()

    vault = resolve_vault_path(args.vault)
    if not vault.is_dir():
        print(f"Vault missing: {vault}")
        print("Run: python scripts/vault_cli.py init   or   /vault-init")
        return 1

    print(render_creative_dashboard(vault, include_github=not args.no_github))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
