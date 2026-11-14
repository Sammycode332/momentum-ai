# Deployment and operational runbook — development candidate

These are preparation instructions, not evidence of a deployed release. No hosting,
production branch, domain, provider budget or retention schedule has been approved.
Container runtime verification is pending: Docker Desktop's Linux engine was not running.

## Topology

HTTPS ingress → frontend Nginx container → private FastAPI service named `api:8000`.
Neon Auth is accessed by the browser; FastAPI verifies its JWTs using configured
JWKS and issuer. FastAPI uses a restricted Neon connection. A separate scheduled
worker uses its own login and only the scheduler grants. Gemini is backend-only.

This same-origin topology needs no cross-origin API allowance. Do not add wildcard
CORS to work around deployment mistakes. Register the exact frontend HTTPS origin
in Neon Auth. Verify OAuth callbacks and password recovery with the configured
provider before advertising those capabilities.

## Build and secrets

- Backend build context: `backend`; Dockerfile installs the optional push extra and
  runs as a non-root user. Supply secrets through hosting-managed environment values.
- Frontend build context: `frontend`; public build arguments `VITE_NEON_AUTH_URL`
  and optional `VITE_SUPPORT_EMAIL`. The frontend listens on 8080 and proxies to `api`.
- Both contexts exclude local environment files. Never pass backend secrets as
  frontend build arguments. Verify the built browser bundle before release.
- Configure TLS at ingress. Only the frontend should be internet-facing; keep the
  backend port private. Configure real-client-IP forwarding with explicitly trusted
  ingress ranges before relying on IP rate limits. The proxy's CSP permits HTTPS
  connections for Neon; narrow this to verified origins for the selected deployment.
- Backend packages currently use ranges, not a complete lockfile; lock and scan
  the tested resolved dependency set before a production release. Pin image digests
  and CI actions to reviewed revisions as part of that release process.

## Database release

1. Select the intended environment/branch and confirm backup/restore availability.
2. Review the outstanding migration diff and role grants. Check catalog state;
   do not infer successful migration application from filenames.
3. Apply only unapplied migrations using the schema owner on a disposable branch
   first. Run controlled two-user RLS tests there. Never use a privileged URL as
   the application runtime connection.
4. Migration 009 creates `momentum_scheduler` as a restricted NOLOGIN group.
   A role administrator provisions a separate non-superuser, non-BYPASSRLS worker
   login and grants that login membership. Never grant it to `momentum_app`.
5. Apply additive migrations on the approved target, then deploy compatible code.
   Current candidate requires 001–012. Migration 012 adds owner-integrity constraints
   to push delivery references and should follow 011.
6. Run the read-only schema audit and synthetic smoke workflows. Record branch,
   timestamp, migration hashes, operator and result without connection secrets.

Rollback application versions first; retain additive tables/data. Do not drop
columns or tables containing user data as an automatic rollback. Restoring a
backup requires a reviewed recovery plan and reconciliation of writes since it.

## Reminders and push

Configure a supervised job to run `python -m app.reminder_worker` once per minute.
It processes bounded batches using row locks, persists notifications and commits
before attempting push. Alert on nonzero exit, job absence or growing backlog.

Push requires `pip install '.[push]'`, securely generated VAPID keys and a valid
`VAPID_SUBJECT`. Keep the private key only in backend/worker secret storage. The
public key is delivered to authenticated browsers. Preserve the keypair across
deployments; key rotation requires a subscription renewal procedure.

Users explicitly enable device notifications. Subscriptions are owner-scoped;
payloads contain generic text. Failed endpoints returning 404/410 are removed.
Other transient failures retry with exponential delay, up to five attempts. Quiet
hours and notification preferences are checked before dispatch. Deliveries older
than one day are not retried. External delivery is at-least-once; a worker crash
after a push succeeds but before commit can cause another push. The notification
tag reduces duplicate display; this is not an exactly-once guarantee.

Test on synthetic desktop/mobile devices. The minimal manifest uses an SVG icon;
complete platform-specific installation/icon validation before marketing a PWA.
iOS Home Screen installation, push permission, offline behavior and delivery have
not been verified here. No email delivery is implemented.

## Monitoring and incidents

- `/health/live` checks process availability only. Run schema/connectivity checks
  privately and schedule a synthetic authenticated journey in staging.
- Log request references, route templates, status and safe error codes. Do not
  enable request/response body logging, raw JWT logging or verbose push SDK logs.
- Alert on sustained 401/5xx, Gemini timeouts/rate limits, failed jobs and pending
  push backlog. Alert thresholds depend on the deployment baseline and traffic.
- Correlate reported failures with `X-Request-ID`; never ask users to send tokens.
- Revoke compromised credentials, disable the affected integration, preserve safe
  operational evidence and restore using reviewed procedures. Verify tenant
  isolation before re-enabling access.
- Confirm Neon backup retention and perform an actual restore rehearsal. A
  configured backup option alone is not evidence of recoverability.

## Costs and release blockers

Hosting, Neon usage, Gemini tokens, worker execution and optional email may incur
costs. No new paid service is provisioned by these templates. Set provider-level
budgets and alerts; per-user request limits do not cap aggregate spend. Remotive
uses a shared six-hour cache and attribution; only jobs/internships are supported.

Full account deletion, provider/audit/backup retention, final support ownership,
legal drafts, live authentication diagnosis, new-schema isolation and real browser
evidence remain release gates. See release-checklist.md.

## Authentication activation

Password recovery now uses Neon SDK methods with a same-origin return address. Verify delivery, expired links, existing-session recovery and callback origin handling with a synthetic account. Google UI is hidden unless VITE_GOOGLE_SIGN_IN_ENABLED=true at build time; enable only after provider configuration and an actual login test. Source reference: [Neon OAuth setup](https://neon.com/docs/auth/guides/setup-oauth) and the installed @neondatabase/auth SDK contracts. No recovery email or OAuth authorization was triggered by automated tests.
