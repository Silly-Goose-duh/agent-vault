# Agent Vault

**Quiet personal memory for coding agents.** Install once, work normally.
No Obsidian app required — just a local markdown folder.

A **quiet watcher** (local script, not a chatty LLM subagent every turn) scans
each prompt for durable facts and secrets, seals them under `me/.private/`,
and `/vault` opens a creative dashboard of everything non-secret.

> Grok Build plugin · Hermes plugin · plain CLI for any agent  
> Repo name is historical (`grok-build-obsidian-plugin`); product is **Agent Vault**.

## Idea (evaluated)

| Approach | Verdict |
|----------|---------|
| Spawn an LLM subagent on **every** prompt | ❌ Latency, cost, secrets re-sent to a model |
| Silent **local** watcher (regex + file merge) on every prompt | ✅ Fast, private, fail-open |
| Agent skill persona (`vault-watcher`) for judgmental merges | ✅ Complements hooks when the main model notices nuance |
| Obsidian dependency | ❌ Unnecessary — plain markdown is enough |

So: **hooks = automatic**, **skill/agent = smart backup**, **dashboard = human face**.

## Install

### Grok Build

```bash
grok plugin install Silly-Goose-duh/grok-build-obsidian-plugin --trust
```

### Hermes

```bash
hermes plugins install Silly-Goose-duh/grok-build-obsidian-plugin --enable
# new session / gateway restart
```

### Any agent (CLI)

```bash
git clone https://github.com/Silly-Goose-duh/grok-build-obsidian-plugin.git
cd grok-build-obsidian-plugin
python scripts/vault_cli.py init
python scripts/quiet_watcher.py --text "My name is Ada. I prefer short answers." --verbose
python scripts/vault_status.py
```

## How it feels day-to-day

1. You code / chat as usual.  
2. After each prompt the **quiet watcher** runs (Grok hooks / Hermes `pre_llm_call`).  
3. Facts land in `me/`, secrets in `me/.private/` (never echoed raw).  
4. `/vault` → creative dashboard of you, todos, reminders, projects, sealed-key count, recent captures.  
5. `/vaultkeys` → labels only.

## Commands

| Command | Purpose |
|---------|---------|
| `/vault` | Creative dashboard (all non-secret contents) |
| `/vaultkeys` | Sealed key labels only |
| `/vault-remember` | Manual save |
| `/vault-todo` | Open todos |
| `/vault-init` | Create / repair vault |
| `/vault-preview` | Local HTTP preview (`.private` blocked) |

## Layout

```text
~/AgentVault/          # or legacy ~/Grok Build if it already exists
  AGENTS.md
  me/
    about-me.md
    preferences.md
    reminders.md
    .private/secrets.local.md
  projects/
  todos/TODO.md
  sessions/activity-YYYY-MM-DD.log
```

## Security

- Secrets: **plaintext on disk**, deep path, gitignored  
- Prefer BitLocker / FileVault / LUKS  
- Dashboard & context injection never include secret values  
- Not a password manager  

See [docs/SECURITY.md](docs/SECURITY.md).

## Dev

```bash
python -m unittest discover -s tests -v
grok plugin validate .
```

## License

MIT — [Silly-Goose-duh](https://github.com/Silly-Goose-duh)
