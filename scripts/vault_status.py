#!/usr/bin/env python3
"""Print a rich vault dashboard (no secret values)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_vault import (  # noqa: E402
    count_secret_rows,
    format_box,
    list_github_repos,
    list_open_todos,
    list_reminders,
    parse_about_simple,
    resolve_vault_path,
    secrets_file,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Vault status dashboard")
    parser.add_argument("--vault", help="Override vault path")
    parser.add_argument(
        "--no-github",
        action="store_true",
        help="Skip GitHub repo listing (no gh call)",
    )
    args = parser.parse_args()

    vault = resolve_vault_path(args.vault)
    if not vault.is_dir():
        print(f"Vault missing: {vault}")
        print("Run ensure_vault.py / vault_cli.py init / /vault-init first.")
        return 1

    todos = list_open_todos(vault)
    secrets_n = count_secret_rows(vault)
    about = parse_about_simple(vault)
    reminders = list_reminders(vault)
    gh_repos = [] if args.no_github else list_github_repos()
    sec_path = secrets_file(vault)

    print("=== Personal Agent Vault ===")
    print(f"Path: {vault}")
    print(f"Secrets file: {sec_path} (values never shown here)")
    print()

    print("## Todos")
    if todos:
        for t in todos:
            print(f"- [ ] {t}")
    else:
        print("- (none open)")
    print()

    print("## GitHub projects (highlights)")
    if args.no_github:
        print("- (skipped)")
    elif gh_repos:
        for name in gh_repos:
            print(f"- {name}")
    else:
        print("- (none found — is `gh` installed and authenticated?)")
    print()

    print("## Reminders")
    print(format_box(reminders if reminders else []))
    print()

    print("## Personal info")
    if about:
        for fact in about:
            print(f"- {fact}")
    else:
        print("- (empty — fill me/about-me.md or use /vault-remember)")
    print()

    print("## Keys")
    print(f"- {secrets_n} stored (values hidden) — use /vaultkeys or `vault_cli.py keys`")
    print()

    print("Commands: /vault-todo  /vault-remember  /vaultkeys  /vault-preview")
    print("CLI: python scripts/vault_cli.py {init,status,keys,remember,capture,context}")
    print("Ask: anything you want added to Reminders?")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
