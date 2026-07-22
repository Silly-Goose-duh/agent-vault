---
description: Show Grok Build vault dashboard (path, todos, secret count)
---

Show the vault dashboard.

1. Run `python "$GROK_PLUGIN_ROOT/scripts/ensure_vault.py"` if needed, then `python "$GROK_PLUGIN_ROOT/scripts/vault_status.py"`.
2. Optionally read `me/about-me.md` and `todos/TODO.md` for a short human summary.
3. **Never** print contents of `me/secrets.local.md` values — only a count if useful.
4. Mention `/vault-todo`, `/vault-remember`, `/vault-preview`.
