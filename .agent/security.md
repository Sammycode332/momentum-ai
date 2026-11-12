# Security Requirements

Security and multi-user data isolation are foundational release criteria, not later hardening.

## Identity and access

- Use Supabase Auth for authentication. Verify credentials in the backend for every private API request and derive the acting user from verified claims.
- Authorize every private resource/action server-side. Reject client-supplied ownership assertions unless they match verified identity and authorization rules.
- Enable and test PostgreSQL RLS for every user-owned table. Default to deny; write explicit owner-scoped policies.
- Frontend route guards, hidden controls, and client filtering improve usability only; they are not security boundaries.

## Data and API protection

- Validate and constrain all inputs at the API boundary; use parameterized database access and safe error responses.
- Return the minimum authorized data. Avoid exposing internal identifiers, tokens, prompts, provider diagnostics, or other users’ data.
- Require authentication and authorization before AI-context retrieval, memory reads/writes, and agent-driven task changes.
- Audit memory approval events and autonomous actions with actor, target, time, outcome, and reversal information while minimizing sensitive data in logs.

## Secrets, AI, and operations

- Store secrets only in environment-managed configuration; never commit them, expose them in browser bundles, include them in prompts/logs/errors, or paste them into docs.
- Evaluate AI provider retention, training, regional handling, and contractual controls before production data is sent. Provide only minimum necessary authorized context.
- Treat AI output as untrusted: validate structured data, constrain allowed actions, and require approval where specified.
- Use reviewed migrations, backups/rollback planning, and least privilege. Destructive operations require explicit scope, safeguards, and an operational record.
- Define production logging, monitoring, incident handling, retention/deletion, and environment separation before launch.

## Verification minimum

Before release, demonstrate invalid-token rejection, tenant isolation for all CRUD operations at API and RLS layers, no secret leakage in repository/client bundle/log samples, validated AI outputs, memory approval enforcement, and autonomous-action boundary/recovery behavior.
