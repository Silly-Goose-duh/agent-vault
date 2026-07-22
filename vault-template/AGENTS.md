# Grok Build Vault Rules

This vault is the user's personal knowledge base for Grok Build sessions.

## Always

- Read `me/about-me.md` when personal context matters.
- Read `todos/TODO.md` when asked about tasks or starting work.
- After important decisions, update the relevant note (do not only chat).
- Keep personal facts in `me/`, project status in `projects/`, work items in `todos/TODO.md`.
- Prefer checklist format: `- [ ]` open, `- [x]` done.

## Auto-capture

When the user shares durable facts about themselves (name, role, timezone, preferences, constraints), merge them into `me/about-me.md` under the right heading. Do not duplicate existing lines.

When the user shares **secrets** (API keys, tokens, passwords, private IDs, connection strings):

1. Append them to `me/secrets.local.md` (create from the example if missing).
2. **Never** repeat the full secret back in chat after saving; mask as `prefix…****`.
3. Never commit `secrets.local.md` or put secrets in git-tracked notes.

## Todos

- Format open items as `- [ ] ...`
- Completed as `- [x] ...`
- When finishing work, mark todos done in `todos/TODO.md`.

## Projects

- One note per project under `projects/<slug>.md`
- Keep `projects/_index.md` updated with status links
