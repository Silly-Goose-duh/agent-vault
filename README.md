# grok-build-obsidian-plugin

Personal **Grok Build** vault plugin: creates a local Obsidian-compatible knowledge base (`me/`, `projects/`, `todos/`), auto-captures personal facts and secrets, and exposes slash commands so Grok can use the vault every session.

> **Not** an Obsidian community plugin. It is a [Grok Build](https://x.ai/build) plugin that manages a markdown folder you can also open in Obsidian.

## Install

Requires [Grok Build](https://x.ai/build) and **Python 3** on your `PATH`.

```bash
grok plugin install Silly-Goose-duh/grok-build-obsidian-plugin --trust
```

Enable the plugin if needed:

```bash
grok plugin enable grok-build-obsidian
```

Or from `/plugins` in the TUI.

### Local / dev install

```bash
git clone https://github.com/Silly-Goose-duh/grok-build-obsidian-plugin.git
grok plugin install ./grok-build-obsidian-plugin --trust
```

## First run

1. Start `grok` (any directory).
2. `SessionStart` runs `ensure_vault.py` and creates:

   - **Windows:** `%USERPROFILE%\Grok Build`  
   - **macOS / Linux:** `~/Grok Build`

3. Check status:

```text
/vault
```

4. Optional — open the folder in Obsidian: **Open folder as vault**.

### Custom vault path

```bash
# permanent for your shell
export GROK_VAULT_PATH="/path/to/My Vault"   # Windows PowerShell: $env:GROK_VAULT_PATH = "D:\My Vault"
```

Or:

```text
/vault-init
```

(and ask Grok to pass `--vault` to the script).

## Commands

| Command | Purpose |
|---------|---------|
| `/vault-init` | Create / repair the vault |
| `/vault` | Dashboard (path, open todos, secret **count** only) |
| `/vault-todo` | List / work open todos |
| `/vault-remember` | Save a personal fact (or secret, masked) |
| `/vault-preview` | Local HTTP preview at `http://127.0.0.1:8765/` |

## Vault layout

```text
Grok Build/
  AGENTS.md
  me/
    about-me.md
    preferences.md
    secrets.local.md      # gitignored — local only
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
| Name, prefs, role, timezone | `me/about-me.md` |
| Todos / next work | `todos/TODO.md` |
| API keys, tokens, passwords, IDs | `me/secrets.local.md` |

Layers:

1. **Skill + AGENTS.md** — Grok merges facts while chatting  
2. **Hooks** — `UserPromptSubmit` / `Stop` run `scripts/auto_capture.py`  
3. **Preview** — secrets are **never** served by the HTTP preview  

See [docs/SECURITY.md](docs/SECURITY.md).

### Security warning

Secrets are stored in **plaintext on disk**. Use disk encryption. Do not commit `secrets.local.md`. This is not a replacement for a password manager.

## Preview / “side panel”

Grok Build plugins **cannot** inject a native right-side Obsidian panel.

Closest options:

1. `/vault` dashboard in the transcript  
2. `/vault-preview` → browser (or Grok localhost preview if available)  
3. Open the same folder in Obsidian  

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
