# grok-build-obsidian-plugin · agent-vault

Personal **agent vault** plugin: creates a local Obsidian-compatible knowledge base (`me/`, `projects/`, `todos/`), **auto-detects** personal facts and secrets from chat, stores secrets in a **deep protected** folder, and exposes commands so any coding agent can reuse them when needed.

> Not an Obsidian community plugin. It is a [Grok Build](https://x.ai/build) plugin **and** a [Hermes Agent](https://hermes-agent.nousresearch.com/) plugin that manages a markdown folder you can also open in Obsidian. CLI works with Claude Code / Codex / anything that can run Python.

## Install

### Grok Build

Requires [Grok Build](https://x.ai/build) and **Python 3** on your `PATH`.

```bash
grok plugin install Silly-Goose-duh/grok-build-obsidian-plugin --trust
grok plugin enable grok-build-obsidian   # if needed
```

Or local:

```bash
git clone https://github.com/Silly-Goose-duh/grok-build-obsidian-plugin.git
grok plugin install ./grok-build-obsidian-plugin --trust
```

### Hermes Agent

```bash
hermes plugins install Silly-Goose-duh/grok-build-obsidian-plugin --enable
```

Slash commands after enable: `/vault`, `/vaultkeys`.

### Any coding agent (CLI)

```bash
git clone https://github.com/Silly-Goose-duh/grok-build-obsidian-plugin.git
cd grok-build-obsidian-plugin
python scripts/vault_cli.py init
python scripts/vault_cli.py status
python scripts/vault_cli.py remember --text "My name is Ada. I prefer short answers."
python scripts/vault_cli.py context   # non-secret brief for the agent
```

Point the agent at the vault folder (or set `AGENT_VAULT_PATH`). Drop `skills/grok-vault/SKILL.md` into the agent’s skills dir if you want automatic behavior.

## First run

1. Start Grok / Hermes / run `vault_cli.py init`.
2. Vault is created at:
   - existing **`%USERPROFILE%\Grok Build`** / `~/Grok Build` if present, else
   - **`~/AgentVault`**
3. Check status: `/vault` or `python scripts/vault_cli.py status`
4. Optional — Obsidian: **Open folder as vault**.

### Custom vault path

```bash
export AGENT_VAULT_PATH="/path/to/My Vault"
# Windows PowerShell: $env:AGENT_VAULT_PATH = "D:\My Vault"
# aliases: GROK_VAULT_PATH, HERMES_VAULT_PATH, VAULT_PATH
```

## Commands

| Command | Purpose |
|---------|---------|
| `/vault-init` | Create / repair the vault |
| `/vault` | Dashboard: todos, GitHub highlights, reminders box, personal info, key **count** |
| `/vaultkeys` | List stored keys (**labels only** — never values) |
| `/vault-todo` | List / work open todos |
| `/vault-remember` | Save a personal fact, reminder, or secret (masked) |
| `/vault-preview` | Local HTTP preview at `http://127.0.0.1:8765/` |

Hermes: `/vault` and `/vaultkeys` (plugin slash commands).

## Vault layout

```text
Grok Build/   or   AgentVault/
  AGENTS.md
  me/
    about-me.md
    preferences.md
    reminders.md
    .private/
      secrets.local.md   # deep + gitignored — local only
  projects/
    _index.md
  todos/
    TODO.md
  sessions/
  .obsidian/
```

## Auto-detect & auto-remember

| What you share | Where it goes |
|----------------|---------------|
| Name, prefs, role, timezone, email | `me/about-me.md` |
| Todos / next work | `todos/TODO.md` |
| Reminders | `me/reminders.md` |
| API keys, tokens, passwords, IDs | `me/.private/secrets.local.md` |

Layers:

1. **Skill + AGENTS.md** — agent merges facts while chatting  
2. **Grok hooks** — `UserPromptSubmit` / `Stop` run `scripts/auto_capture.py`  
3. **Hermes hooks** — `pre_llm_call` scans the user message; first turn injects non-secret context  
4. **CLI** — `vault_cli.py capture|remember`  
5. **Preview** — secrets and `.private` are **never** served  

See [docs/SECURITY.md](docs/SECURITY.md).

### Security warning

Secrets are stored in **plaintext on disk** under a hidden folder. Use disk encryption. Do not commit secrets. This is not a password manager.

## Development

```bash
cd grok-build-obsidian-plugin
python -m unittest discover -s tests -v
grok plugin validate .
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## License

MIT — see [LICENSE](LICENSE).

## Author

[Silly-Goose-duh](https://github.com/Silly-Goose-duh)
