---
description: Save a personal fact into me/about-me.md (non-secret)
---

Save durable personal context into the vault.

1. Ensure vault exists (`ensure_vault.py`).
2. Take the user's text after the command (or ask what to remember).
3. If it is a **secret** (API key, password, token), append to `me/secrets.local.md` and reply masked.
4. Otherwise merge a clear bullet into `me/about-me.md` under Identity / Preferences / Constraints / Notes.
5. Confirm what was saved (masked if secret).
