#!/usr/bin/env python3
"""List stored vault keys metadata only (never values)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_vault import list_secret_keys, resolve_vault_path, secrets_file  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="List vault key labels (no values)")
    parser.add_argument("--vault", help="Override vault path")
    args = parser.parse_args()

    vault = resolve_vault_path(args.vault)
    if not vault.is_dir():
        print(f"Vault missing: {vault}")
        print("Run ensure_vault.py or /vault-init first.")
        return 1

    keys = list_secret_keys(vault)
    print("=== Vault keys (values never shown) ===")
    print(f"Path: {vault}")
    print(f"Secrets file: {secrets_file(vault)}")
    print(f"Count: {len(keys)}")
    print()
    if not keys:
        print("(no keys stored yet)")
        print("Paste a secret in chat or: python scripts/vault_cli.py remember --kind secret '…'")
        return 0

    print(f"{'When (UTC)':<22} {'Kind':<14} {'Label':<24} Source")
    print("-" * 72)
    for k in keys:
        print(f"{k['when']:<22} {k['kind']:<14} {k['label']:<24} {k['source']}")
    print()
    print("Values stay on disk only under me/.private/. Never printed here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
