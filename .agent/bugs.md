# Reproducible defect register

| ID | Evidence / reproduction | Status and next check |
| --- | --- | --- |
| BUG-001 | Owner reports initial Overview access-token rejection, then success after retries. Installed Neon adapter injects `set-auth-jwt` into session token and supports uncached `X-Force-Fetch`. Frontend already coalesces acquisition and refreshes stale/opaque JWTs. | Open: capture failing status/request reference and verifier reason; no confirmed live root cause. Do not add delays or weaken verification. |
| BUG-002 | `Workspace.signOut` ignored returned errors and did not catch thrown errors; failure provided no feedback. | Fixed, automated regression verified for both SDK failures and retry. Browser sign-out verification pending. |
| BUG-003 | Initial `getSession()` rejection escaped safe error mapping. | Fixed, rejection/redaction/recovery test passed; no API replay. |
| BUG-004 | Core record descriptions had no length bound; NUL text reached PostgreSQL. | Fixed at API boundary; POST/PUT regressions across domains passed. Existing records unchanged. |
| BUG-005 | Workspace displayed “All systems ready” without health evidence. | Replaced with neutral workspace label. |
| BUG-006 | Initial bundle included assistant/Markdown (533.71 kB JS). | Lazy loading reduced initial JS to 403.99 kB; build passes. Browser assistant-navigation check pending. |

No zero-bug or production-readiness claim is warranted. Network, signed-in lifecycle, cross-user SQL and responsive checks remain release gates.


- BUG-RC-009: user reproduced migration 009 SQLSTATE 42704 (scheduler role absent). Root cause: draft only documented manual role creation. Fixed migration to create restricted NOLOGIN role before policies and validate role safety. Recovery documented in migrations/README.md. Live retry unverified.
- BUG-RC-010: code review found disabled personalization passed an empty context into alias_context, which indexed missing task/project keys. Fixed optional-key handling. Regression test confirms no private retrieval when disabled; passed.

- BUG-RC-011 (confirmed 2026-11-14): onboarding GET 503 reported by user. Read-only connection diagnostic using backend/.env and runtime momentum_app failed with OperationalError categorized DB_CREDENTIALS, before any table query. Configuration source is backend/.env (not this tool process environment). Requires updating the runtime connection credential for the intended development branch and restarting the server. No credential printed or changed; no migration rerun. Added app.storage_diagnostic for repeatable sanitized checks.

- BUG-RC-012: the assistant said it added a high-priority task for tomorrow at 6 PM, but Tasks showed no record. Code review confirmed that chat persisted provider prose and never invoked the proposal or approval path. Saved chat now extracts a typed task proposal and shows an explicit approval card. Only a successful, committed approval with a task ID produces the task-created status. General replies and historical chat display filter recognizable unconfirmed execution claims. The original request trace was unavailable.
