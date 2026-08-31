# Security Policy

Portable AI Memory is designed to process highly sensitive conversation history. Security and privacy reports are treated as first-class project issues.

## Never include private memory in a report

Do not paste real chat exports, private messages, database files, API keys, capability tokens, credentials, or other personal data into a public GitHub issue.

When reporting a bug, use synthetic data or a minimal redacted reproduction.

## Sensitive areas

Please pay particular attention to vulnerabilities involving:

- unauthorized MCP/API access
- capability-token leakage
- path traversal or arbitrary file access
- accidental serving of canonical exports or SQLite/Postgres data
- prompt or query paths that expose unrelated private records
- insecure deployment defaults
- logging of message content or secrets
- importer behavior that corrupts or silently drops source data

## Deployment guidance

Production deployments should keep memory data outside public web roots, use authentication for every read endpoint, store secrets in environment variables or a secret manager, and encrypt private storage where supported.

This project does not require users to upload their conversation corpus to a project-operated service. Self-hosting and user-controlled storage are core design goals.
