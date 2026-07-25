# Security

## Secrets

```text
<vault>/me/.private/secrets.local.md
```

- Deep hidden folder, gitignored  
- Plaintext convenience store — use disk encryption  
- Never served by preview HTTP  
- Never injected into agent context (counts/labels only)  
- Quiet watcher logs **masked** summaries only to `sessions/activity-*.log`

## Capture surface

Automatic patterns: `sk-…`, `xai-…`, `ghp_/gho_…`, AWS `AKIA…`, Bearer/JWT,
`password=`, DB URIs, plus phrases like “my name is…”, “I prefer…”.

## Chat hygiene

After seal → mask only (`sk-…****`). Fail-open hooks never block the session.

## Not included

Password-manager grade encryption, cloud sync, multi-user ACLs.
