---
name: agent-vault
description: >-
  Quiet personal vault for coding agents (no Obsidian). Auto-captures facts and
  secrets from chat into a local markdown vault; /vault creative dashboard.
  Use when user mentions vault, remember this, personal details, API keys, or /vault.
---

# Agent Vault Skill

## Idea

Install once → work normally. A **quiet watcher** (local script hooks + this skill)
checks each prompt for durable details and sealed secrets. No Obsidian app needed —
just folders of markdown under `~/AgentVault` (or legacy `~/Grok Build`).

## Paths

1. `AGENT_VAULT_PATH` / `GROK_VAULT_PATH` / `HERMES_VAULT_PATH`
2. plugin `config.json` → `vault_path`
3. existing `~/Grok Build` else `~/AgentVault`

```bash
python "$GROK_PLUGIN_ROOT/scripts/ensure_vault.py"
python "$GROK_PLUGIN_ROOT/scripts/quiet_watcher.py" --text "..." --source skill
python "$GROK_PLUGIN_ROOT/scripts/vault_status.py"   # creative dashboard
```

## Layout

```text
AgentVault/
  AGENTS.md
  me/about-me.md
  me/preferences.md
  me/reminders.md
  me/.private/secrets.local.md   # deep + local only
  projects/
  todos/TODO.md
  sessions/activity-*.log        # masked capture log
```

## Quiet behavior

- Do not interrupt the user's coding flow.
- Merge facts under headings; no duplicate bullets.
- Secrets → `.private` only; reply masked if you must acknowledge.
- Hooks run `quiet_watcher.py` automatically (Grok + Hermes).

## /vault

Always run `vault_status.py` and show the full creative frame. Never values from secrets.

## Commands

- `/vault` dashboard · `/vaultkeys` labels · `/vault-remember` · `/vault-todo` · `/vault-init` · `/vault-preview`
