---
description: Save a personal fact into me/about-me.md (non-secret) or deep secrets
---

Save durable personal context into the vault.

1. Ensure vault exists (`ensure_vault.py` or `vault_cli.py init`).
2. Take the user's text after the command (or ask what to remember).
3. Classify:
   - **Secret** (API key, password, token) → append row to `me/.private/secrets.local.md`; reply **masked** only.
   - **Reminder** / short note to self → append `- [ ] …` under Active in `me/reminders.md`.
   - **Personal fact** → merge a clear bullet into `me/about-me.md` (Identity / Preferences / Constraints / Notes).
4. Confirm what was saved (masked if secret).

Optional CLI:

```bash
python "$GROK_PLUGIN_ROOT/scripts/vault_cli.py" remember --text "..."
python "$GROK_PLUGIN_ROOT/scripts/vault_cli.py" remember --kind secret --label resend "re_..."
python "$GROK_PLUGIN_ROOT/scripts/vault_cli.py" remember --kind reminder "Pay rent Friday"
```
