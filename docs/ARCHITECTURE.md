# Architecture

## Overview

This repo is a **multi-agent personal vault plugin**:

| Surface | How it loads |
|---------|----------------|
| **Grok Build** | `plugin.json` + `hooks/hooks.json` + `skills/` + `commands/` |
| **Hermes Agent** | `plugin.yaml` + root `__init__.py` (`register(ctx)`) |
| **Any agent** | Shell out to `scripts/vault_cli.py` + read `vault-template` / live vault |

It scaffolds a local markdown vault and teaches agents how to use it. You can open the same folder in Obsidian.

```
┌──────────────────────┐   file tools / hooks   ┌──────────────────────────┐
│ Grok / Hermes / CLI  │ ─────────────────────► │  ~/Grok Build or         │
│ + this plugin        │ ◄───────────────────── │  ~/AgentVault            │
└──────────┬───────────┘                        │  (Obsidian-compatible)   │
           │                                    └────────────┬─────────────┘
           │ scripts/*.py                                    │ optional
           ▼                                                 ▼
   ensure / capture / status                            Obsidian app
```

## Components

| Component | Role |
|-----------|------|
| `vault-template/` | Seed files copied on first run |
| `scripts/ensure_vault.py` | Idempotent vault creation + deep secrets migrate |
| `scripts/auto_capture.py` | Heuristic secret + personal fact capture |
| `scripts/vault_status.py` | Dashboard (no secret values) |
| `scripts/vault_keys.py` | Key metadata list only |
| `scripts/vault_cli.py` | Unified CLI for any agent |
| `scripts/preview_server.py` | Local HTTP note browser (blocks `.private`) |
| `hooks/hooks.json` | Grok SessionStart + UserPromptSubmit + Stop |
| `__init__.py` | Hermes hooks + `/vault` slash commands |
| `skills/grok-vault/` | Agent instructions |
| `commands/` | Grok slash command markdown |

## Path resolution

1. `--vault` CLI flag  
2. `AGENT_VAULT_PATH` / `GROK_VAULT_PATH` / `HERMES_VAULT_PATH` / `VAULT_PATH`  
3. plugin data `config.json` → `vault_path`  
4. Existing `~/Grok Build` if present, else `~/AgentVault`

## Secrets (deep + protected)

Preferred path:

```text
<vault>/me/.private/secrets.local.md
```

- Hidden folder + gitignored  
- Owner-only mode bits on POSIX (`0o600` / `0o700`)  
- Legacy `me/secrets.local.md` is migrated once on ensure  
- Preview HTTP **never** serves `.private` or secrets files  
- Values are **never** injected into agent context (only counts / labels)

## Hermes hooks

- `on_session_start` → ensure vault  
- `pre_llm_call` → scan `user_message`; on first turn inject non-secret `brief_context_for_agent`

## Why not a native side panel?

Grok plugins can ship skills, commands, hooks, MCP, and LSP — **not** custom TUI chrome. Preview is approximated via `/vault`, `/vault-preview`, or Obsidian.
