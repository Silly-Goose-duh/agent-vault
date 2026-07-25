# Agent Vault Rules

This vault is the user's personal knowledge base for coding-agent sessions
(Grok Build, Hermes, Claude Code, Codex, etc.).

## Always

- Read `me/about-me.md` when personal context matters.
- Read `todos/TODO.md` when asked about tasks or starting work.
- After important decisions, update the relevant note (do not only chat).
- Keep personal facts in `me/`, project status in `projects/`, work items in `todos/TODO.md`, reminders in `me/reminders.md`.
- Prefer checklist format: `- [ ]` open, `- [x]` done.
- On `/vault`, list todos, GitHub highlight names only, reminders in a box, simple personal info; never print secret values (use `/vaultkeys` for labels only).

## Auto-capture

When the user shares durable facts about themselves (name, role, timezone, preferences, constraints), merge them into `me/about-me.md` under the right heading. Do not duplicate existing lines.

When the user shares **secrets** (API keys, tokens, passwords, private IDs, connection strings):

1. Append them to `me/.private/secrets.local.md` (create via ensure_vault if missing).
2. **Never** repeat the full secret back in chat after saving; mask as `prefix…****`.
3. Never commit secrets or put them in git-tracked notes.
4. Prefer the deep path `me/.private/` — not the vault root.

## Todos

- Format open items as `- [ ] ...`
- Completed as `- [x] ...`
- When finishing work, mark todos done in `todos/TODO.md`.

## Projects

- One note per project under `projects/<slug>.md`
- Keep `projects/_index.md` updated with status links
