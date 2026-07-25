---
description: Save a personal fact, reminder, or sealed secret
---

Save durable personal context into the Agent Vault.

1. Ensure vault exists.
2. Take text after the command (or ask what to remember).
3. Classify:
   - **Secret** → `me/.private/secrets.local.md` · reply masked only
   - **Reminder** → `me/reminders.md` as `- [ ] …`
   - **Fact** → `me/about-me.md`
4. Or run: `python "$GROK_PLUGIN_ROOT/scripts/quiet_watcher.py" --text "..." --source remember --verbose`
