---
description: Create or repair the local personal agent vault on disk
---

Ensure the user's personal agent vault exists.

1. Run: `python "$GROK_PLUGIN_ROOT/scripts/ensure_vault.py"` (on Windows, `python` or `py -3` is fine).
2. If the user passed a path argument, use `--vault <path>`.
3. Then run `python "$GROK_PLUGIN_ROOT/scripts/vault_status.py"` and summarize:
   - absolute vault path
   - open todo count
   - secrets path (`me/.private/…`) without values
   - how to open the folder in Obsidian ("Open folder as vault")
4. Do not print any secret values.
