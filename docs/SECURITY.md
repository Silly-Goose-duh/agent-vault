# Security

## Secrets storage

Captured API keys, tokens, and passwords are written to:

```text
<vault>/me/.private/secrets.local.md
```

Properties:

- **Deep path** under hidden `.private/` (not vault root)
- **Local disk only** (gitignored in template and repo)
- **Plaintext** — convenience capture, not a password manager
- Prefer full-disk encryption (BitLocker, FileVault, LUKS)
- POSIX: best-effort `0o600` file / `0o700` dir permissions
- Preview server **never** serves `.private/` or `secrets.local.md`
- Agent context injection includes **counts only**, never values
- `/vaultkeys` prints labels only

## What is auto-captured

Heuristic patterns include (non-exhaustive):

- `sk-…`, `xai-…`, OpenRouter-style keys  
- `ghp_…`, `gho_…`, `github_pat_…`  
- `AKIA…` AWS access key IDs  
- `Bearer …` tokens, JWTs  
- `password=` assignments  
- Connection URIs (`postgres://`, `mongodb://`, …)  

Personal phrases such as “my name is …”, “I prefer …”, emails.

## What is never published

The public GitHub repo contains only **templates and code**. Runtime vaults and secrets must not be committed.

Before every push, scan:

```bash
git grep -E "sk-[A-Za-z0-9]{10,}|ghp_|gho_|xai-" || true
```

## Chat hygiene

After saving a secret, the agent and hooks should reply with **masked** values only (`sk-…****`).

## Limitations

- Regex capture can miss unusual secret formats or false-positive  
- Model skill capture depends on the agent following instructions  
- Hooks fail open (never block the session if Python errors)  
- This is **not** a substitute for a password manager or KMS  
