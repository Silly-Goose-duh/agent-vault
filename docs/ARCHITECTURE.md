# Architecture

## Overview

`grok-build-obsidian` is a **Grok Build plugin** (not an Obsidian community plugin). It scaffolds a local markdown vault and teaches Grok how to use it.

```
┌─────────────────┐     file tools      ┌──────────────────────┐
│  Grok Build TUI │ ─────────────────► │  ~/Grok Build vault  │
│  + this plugin  │ ◄───────────────── │  (Obsidian-compatible)│
└────────┬────────┘                     └──────────┬───────────┘
         │ hooks                                   │
         │ ensure_vault / auto_capture             │ optional open
         ▼                                         ▼
   scripts/*.py                               Obsidian app
```

## Components

| Component | Role |
|-----------|------|
| `vault-template/` | Seed files copied on first run |
| `scripts/ensure_vault.py` | Idempotent vault creation |
| `scripts/auto_capture.py` | Heuristic secret + personal fact capture |
| `scripts/vault_status.py` | Dashboard (no secret values) |
| `scripts/preview_server.py` | Local HTTP note browser |
| `hooks/hooks.json` | SessionStart + UserPromptSubmit + Stop |
| `skills/grok-vault/` | Agent instructions |
| `commands/` | Slash commands |

## Path resolution

1. `--vault` CLI flag  
2. `GROK_VAULT_PATH` env  
3. `$GROK_PLUGIN_DATA/config.json` → `vault_path`  
4. Default: `~/Grok Build`

## Why not a native side panel?

Grok plugins can ship skills, commands, hooks, MCP, and LSP — **not** custom TUI chrome. Preview is approximated via:

- `/vault` text dashboard  
- `/vault-preview` HTTP UI  
- Opening the same folder in Obsidian  

## Multi-developer install

Each developer runs `grok plugin install … --trust`. On first session, `SessionStart` creates **their** vault under their home directory. No shared personal data.
