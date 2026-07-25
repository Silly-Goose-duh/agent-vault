---
description: List stored vault keys (labels only — never secret values)
---

List keys stored in the vault **without revealing values**.

## Steps

1. Ensure vault exists: `python "$GROK_PLUGIN_ROOT/scripts/ensure_vault.py"` if needed.
2. Run `python "$GROK_PLUGIN_ROOT/scripts/vault_keys.py"`.
3. Present the table: **When**, **Kind**, **Label**, **Source** only.
4. **Never** open or print the Value column from `me/.private/secrets.local.md`.
5. If empty, say how to add one (paste a secret in chat, or `/vault-remember`; secrets go under `.private`).

Alias intent: `/vaultkeys`, "vault keys", "list my keys", "what secrets are stored".
