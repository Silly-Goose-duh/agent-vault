# Agent Vault Rules

Plain-markdown personal memory for coding agents. **No Obsidian required.**

## Quiet watcher (always on)

After every user prompt, a local watcher scans for durable details:

- personal facts → `me/about-me.md` / `me/preferences.md`
- reminders → `me/reminders.md`
- secrets (keys, tokens, passwords) → `me/.private/secrets.local.md`

Do **not** narrate captures unless the user asks. Never echo full secret values — mask as `prefix…****`.

## Always

- Read `me/about-me.md` when personal context matters.
- Read `todos/TODO.md` for open work.
- After important decisions, update the relevant note (not only chat).
- Keep secrets only under `me/.private/`.
- `/vault` shows the creative dashboard (no secret values). `/vaultkeys` = labels only.

## Todos

- `- [ ]` open · `- [x]` done
- Mark done in `todos/TODO.md` when finishing work.

## Projects

- Notes under `projects/<slug>.md`
- Keep `projects/_index.md` current
