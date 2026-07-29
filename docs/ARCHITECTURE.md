# Architecture

## Product decision

**Agent Vault** is Obsidian-free plain markdown. Hooks run a local **quiet watcher**
after every user prompt. An optional Grok `agents/vault-watcher` persona / skill
adds judgment without paying for a full LLM subagent on every turn.

```
 user prompt
     │
     ▼
 ┌───────────────────┐     fail-open      ┌────────────────────┐
 │ quiet_watcher.py  │ ─────────────────► │ ~/AgentVault       │
 │ (local "subagent")│                    │ me/.private/…      │
 └───────────────────┘                    │ sessions/activity  │
     │                                    └─────────┬──────────┘
     │ Hermes pre_llm / Grok hooks                  │
     ▼                                              ▼
  main coding agent                          /vault dashboard
```

## Layers

| Layer | Role |
|-------|------|
| `scripts/quiet_watcher.py` | Silent capture entry (hooks call this) |
| `scripts/auto_capture.py` | Regex extract + file merge |
| `scripts/vault_status.py` | Creative dashboard |
| `agents/vault-watcher.md` | Grok subagent persona (judgment, not forced every token) |
| `skills/agent-vault/` | Instructions for the main model |
| `hooks/hooks.json` | Grok SessionStart / UserPromptSubmit / Stop |
| `__init__.py` | Hermes hooks + `/vault` slash commands |

## Why not LLM-every-prompt?

- Secrets would hit another model call  
- Adds 1–10s latency per turn  
- Breaks “just work” UX  

Local heuristics + skill awareness is the right default. Users can still say
“remember this” for explicit saves.

## Path resolution

`AGENT_VAULT_PATH` → `GROK_VAULT_PATH` → `HERMES_VAULT_PATH` → config →
existing `~/Grok Build` else `~/AgentVault`.
