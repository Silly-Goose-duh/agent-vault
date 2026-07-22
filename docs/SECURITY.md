# Security

## Secrets storage

Captured API keys, tokens, and passwords are written to:

```text
<vault>/me/secrets.local.md
```

Properties:

- **Local disk only** (gitignored in template and repo)
- **Plaintext** — this is convenience capture, not a password manager
- Prefer full-disk encryption (BitLocker, FileVault, LUKS)
- Preview server **never** serves `secrets.local.md`

## What is auto-captured

Heuristic patterns include (non-exhaustive):

- `sk-…`, `xai-…`, OpenRouter-style keys  
- `ghp_…`, `github_pat_…`  
- `AKIA…` AWS access key IDs  
- `Bearer …` tokens, JWTs  
- `password=` assignments  
- Connection URIs (`postgres://`, `mongodb://`, …)  

Personal phrases such as “my name is …”, “I prefer …”.

## What is never published

The public GitHub repo contains only **templates and code**. Runtime vaults and `secrets.local.md` must not be committed.

Before every push, scan:

```bash
git grep -E "sk-[A-Za-z0-9]{10,}|ghp_|xai-" || true
```

## Chat hygiene

After saving a secret, the agent and hooks should reply with **masked** values only (`sk-…****`).

## Limitations

- Regex capture can miss unusual secret formats or false-positive  
- Model skill capture depends on the agent following instructions  
- Hooks fail open (never block the session if Python errors)  
