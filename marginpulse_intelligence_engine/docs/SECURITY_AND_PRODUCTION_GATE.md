# Security and production gate

The current build is designed for local pilot testing and controlled validation. It is not a complete production multi-tenant application.

Before live hosted client processing:

- Replace the shared API key with authenticated users and per-tenant authorisation.
- Enforce deny-by-default access checks on every client and analysis route.
- Use private object storage with short-lived signed links, tenant path boundaries and separate encryption keys where appropriate.
- Add file type validation, malware scanning, decompression-bomb protection, request-size and row-count quotas.
- Add task queue, retries, idempotency, cancellation, monitoring and alerts.
- Define client-approved retention, backup, restoration and deletion procedures.
- Use TLS and managed secrets; never commit `.env` or customer data.
- Add access audit logs and security incident response.
- Pen-test tenant isolation before shared infrastructure is used.
- Review Power BI licensing and row-level security before external client distribution.
- Review local privacy, data-transfer, tax and contractual obligations for each client jurisdiction.

The current filesystem storage separates outputs by normalised client ID, but one service API key can access any client ID. That is not tenant-safe authorisation. Do not expose this API to the public internet as-is.
