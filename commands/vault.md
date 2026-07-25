---
description: Vault dashboard — todos, GitHub projects, reminders box, personal info
---

Show the **personal agent vault dashboard**.

## Steps

1. Run `python "$GROK_PLUGIN_ROOT/scripts/ensure_vault.py"` if the vault may be missing.
2. Run `python "$GROK_PLUGIN_ROOT/scripts/vault_status.py"` and present its output clearly (use the same sections).
3. You may also read files to enrich the human summary:
   - `todos/TODO.md` — open todos
   - `me/about-me.md` + `me/preferences.md` — personal info (simple bullets)
   - `me/reminders.md` — reminders (show inside a markdown/ASCII **box**)
4. **GitHub projects**: list **highlight** repo **names only** (from the script — top original projects, not forks/clones/profile shells). Do not dump every repo.
5. **Never** print contents of `me/.private/secrets.local.md` **values** — only a count. Point to `/vaultkeys` for the key list (labels only).
6. After the dashboard, **ask**: “Anything you want me to add to Reminders?”
   - If they answer with a reminder, append `- [ ] …` under Active in `me/reminders.md` and confirm.
7. Mention related commands: `/vault-todo`, `/vault-remember`, `/vaultkeys`, `/vault-preview`.

## Dashboard sections (required order)

1. **Todos** — list open `- [ ]` items
2. **GitHub projects** — best/highlight names only (not the full list)
3. **Reminders** — box
4. **Personal info** — simple bullets (skip empty placeholders)
5. **Keys** — count + link to `/vaultkeys`
