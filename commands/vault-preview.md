---
description: Local HTTP preview of vault notes (private dir blocked)
---

1. Ensure vault exists.
2. Background: `python "$GROK_PLUGIN_ROOT/scripts/preview_server.py" --port 8765`
3. Open `http://127.0.0.1:8765/`
4. `me/.private/` is never served. No Obsidian required.
