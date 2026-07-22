---
name: grok-vault
description: >-
  Manage the local Grok Build personal vault (Obsidian-compatible markdown):
  about-me, projects, todos, and local secrets capture. Use when the user
  mentions vault, Obsidian, todos, remember this about me, personal notes,
  API keys/tokens to store, or /vault commands.
---

# Grok Vault Skill

## Vault location

1. Prefer env `GROK_VAULT_PATH` if set.
2. Else read `$GROK_PLUGIN_DATA/config.json` → `vault_path`.
3. Else default `~/Grok Build` (Windows: `%USERPROFILE%\Grok Build`).

If unsure, run:

```bash
python "$GROK_PLUGIN_ROOT/scripts/ensure_vault.py"
python "$GROK_PLUGIN_ROOT/scripts/vault_status.py"
```

## Layout

| Path | Purpose |
|------|---------|
| `me/about-me.md` | Non-secret personal facts |
| `me/preferences.md` | Style / workflow prefs |
| `me/secrets.local.md` | **Local only** API keys, tokens, passwords |
| `projects/` | Project notes + `_index.md` |
| `todos/TODO.md` | Source of truth for open work |
| `AGENTS.md` | Standing rules for this vault |

## Auto-capture rules

Whenever the user shares durable personal context, **update** `me/about-me.md` (merge under headings; no duplicate bullets).

Whenever the user pastes secrets (API keys, tokens, passwords, private IDs, connection strings):

1. Append a row to `me/secrets.local.md`.
2. Reply with **masked** values only (`sk-…****`).
3. Never put secrets in git-tracked notes or chat logs if you can avoid it.

Hooks also run `scripts/auto_capture.py` on prompt submit / stop as a backup.

## Todos

- Read and edit `todos/TODO.md` with `- [ ]` / `- [x]`.
- When finishing work the user asked for, mark the matching todo done.

## Commands

- `/vault-init` — ensure vault exists
- `/vault` — dashboard (no secret values)
- `/vault-todo` — list / work open todos
- `/vault-remember` — write a fact into about-me
- `/vault-preview` — local HTTP preview (secrets never served)
