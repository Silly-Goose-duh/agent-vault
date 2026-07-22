---
description: List open vault todos and optionally work the next one
---

Work with `todos/TODO.md` in the Grok Build vault.

1. Resolve vault path via `python "$GROK_PLUGIN_ROOT/scripts/vault_status.py"` or config.
2. Read `todos/TODO.md`.
3. List all open `- [ ]` items.
4. If the user asked to continue or "work next", pick the first Active open todo and start it.
5. When completing work, mark items `- [x]` in the file.
