---
description: Start a local HTTP preview of the vault (secrets not served)
---

Start the vault preview server.

1. Ensure vault exists.
2. Run in background: `python "$GROK_PLUGIN_ROOT/scripts/preview_server.py" --port 8765`
3. Tell the user to open `http://127.0.0.1:8765/` in a browser (or Grok's localhost preview if available).
4. State clearly: `me/.private/` and `secrets.local.md` are **never** exposed by the server.
5. Grok plugins cannot inject a native right-side Obsidian panel; this web preview is the closest built-in option.
