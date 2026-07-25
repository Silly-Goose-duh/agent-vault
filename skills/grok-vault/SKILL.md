---
name: grok-vault
description: >-
  Manage the local personal agent vault (Obsidian-compatible markdown):
  about-me, projects, todos, reminders, and deep local secrets capture. Use when the
  user mentions vault, Obsidian, todos, remember this about me, personal notes,
  API keys/tokens to store, or /vault commands.
---

# Agent Vault Skill

## Vault location

1. Prefer env `AGENT_VAULT_PATH` / `GROK_VAULT_PATH` / `HERMES_VAULT_PATH` if set.
2. Else read plugin data `config.json` → `vault_path`.
3. Else existing `~/Grok Build`, else `~/AgentVault`.

If unsure, run:

```bash
python "$GROK_PLUGIN_ROOT/scripts/ensure_vault.py"
python "$GROK_PLUGIN_ROOT/scripts/vault_status.py"
# or cross-agent:
python "$GROK_PLUGIN_ROOT/scripts/vault_cli.py" status
```

## Layout

| Path | Purpose |
|------|---------|
| `me/about-me.md` | Non-secret personal facts |
| `me/preferences.md` | Style / workflow prefs |
| `me/reminders.md` | Short self-reminders (box on `/vault`) |
| `me/.private/secrets.local.md` | **Deep + local only** API keys, tokens, passwords |
| `projects/` | Project notes + `_index.md` |
| `todos/TODO.md` | Source of truth for open work |
| `AGENTS.md` | Standing rules for this vault |

## Auto-capture rules

Whenever the user shares durable personal context, **update** `me/about-me.md` (merge under headings; no duplicate bullets).

Whenever the user asks to be **reminded** of something, append `- [ ] …` to `me/reminders.md`.

Whenever the user pastes secrets (API keys, tokens, passwords, private IDs, connection strings):

1. Append a row to `me/.private/secrets.local.md`.
2. Reply with **masked** values only (`sk-…****`).
3. Never put secrets in git-tracked notes or chat logs if you can avoid it.

Hooks also run `scripts/auto_capture.py` (Grok) / Hermes `pre_llm_call` as a backup.

## When needed (recall)

Before personalizing work, read `me/about-me.md` + `todos/TODO.md`, or run:

```bash
python scripts/vault_cli.py context
```

## Commands

- `/vault-init` — ensure vault exists
- `/vault` — dashboard: todos, highlight GitHub repos, reminders box, personal info, key **count**
- `/vaultkeys` — list stored keys (**When / Kind / Label / Source** only — never values)
- `/vault-todo` — list / work open todos
- `/vault-remember` — save a personal fact, reminder, or secret (masked)
- `/vault-preview` — local HTTP preview (secrets + `.private` never served)

## Security

- `/vault` and `/vaultkeys` must **never** print secret values.
- Values live only under `me/.private/` on disk.
- Prefer full-disk encryption. Not a password manager.
