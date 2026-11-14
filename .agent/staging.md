# Momentum AI staging and submission plan

The first hosted target is a privately shared synthetic demo on a public HTTPS
URL. It is a Phase 9 checkpoint. The public launch gates in the
[release checklist](release-checklist.md) still apply.

## Hosting and cost

| Option | Estimated monthly infrastructure | Trade-off |
| --- | --- | --- |
| **Recommended** Render Starter Nginx web service and Starter private FastAPI, Frankfurt; fresh Neon Free project | **$14 base** before usage, tax, Gemini or optional services | Managed HTTPS and predictable compute. Keeps the UI and `/api/v1/*` on one HTTPS origin, preserves the proxy's headers and gives FastAPI only a private listener. Two small services are monitored separately. |
| Render Free web service for Nginx, Starter private FastAPI, Neon Free | **$7 base** | Optional cost-down choice for rehearsals. The web service may sleep after 15 minutes idle, take about a minute to return, and draws from 750 shared free instance-hours per workspace per month. Check Render's outbound usage limits. Keep the paid private API; two free web services would lose the private backend boundary. |
| Railway Hobby Nginx and private FastAPI, Neon Free | **$5 minimum** with $5 of usage included; CPU, RAM and egress can raise it | Managed HTTPS and private network, but meter both services and set a usage alert. Railway Cron has a five-minute minimum interval, so matching the existing one-minute schedule needs a separate persistent runner. |

Sources: [Render pricing](https://render.com/pricing), [free limitations](https://render.com/docs/free), [private services](https://render.com/docs/private-services), [Railway pricing](https://docs.railway.com/pricing/plans), [Railway Cron](https://docs.railway.com/cron-jobs), [Neon pricing](https://neon.com/pricing).

Render Cron is the later worker host. Use the API Dockerfile and the Docker
Command `python -m app.reminder_worker` with `* * * * *` UTC. This is a supervised
one-shot process with run history, failure alerts and one active run per job.
Render charges for active time with a $1/month minimum per job. Estimate at least
**$15/month** for the recommended pair plus Cron, before database and usage costs.
The worker is absent from the initial Blueprint. [Render Cron](https://render.com/docs/cronjobs)

Neon Free currently includes 100 CU-hours and 1 GB storage per project with
managed Auth. A one-minute DB job can keep compute awake. At a constant 0.25 CU
for 30 days it would consume about 180 CU-hours. At the listed Launch rate of
$0.106/CU-hour, that's about $19/month in compute alone. Monitor actual Neon,
Render and Gemini usage before enabling the continuous schedule. The per-user AI
limit is independent of total Gemini spend. [Neon pricing](https://neon.com/pricing)

## Step 1 — Create the empty staging project

Step 1 is approved. The owner will create the project in the Console after
reviewing these settings. Use a Free workspace and create `momentum-ai-staging`
in AWS Europe (Frankfurt), `aws-eu-central-1`, with PostgreSQL 17, database
`neondb`, and one default read-write compute with automatic suspension. Name the
fresh default branch `staging`. If the form assigns a branch name, rename the
new project's default branch under **Branches → branch overview → ⋮ → Rename**.
Leave expiration unset. Use the smallest available compute setting; keep the
free limit and scale-to-zero enabled.

From the [Neon Console](https://console.neon.tech/), select a workspace on Free,
click **New Project**, confirm the settings and keep only **Postgres database**
enabled for this checkpoint. Managed Auth, its endpoints and synthetic users
come later. Leave optional services disabled. If the Console calls for a plan
upgrade or shows a charge, stop before creating the project. The published Free
price is $0, with 100 CU-hours per month and 1 GB of Postgres storage per project.
[Project setup](https://neon.com/docs/manage/projects) ·
[Branch rename](https://neon.com/docs/manage/branches#rename-a-branch) ·
[Pricing](https://neon.com/pricing)

Stop after recording the project ID, branch ID and database endpoint hostname
from the new project. These identifiers are sufficient for the handoff. Keep the
new direct owner URL, if saved, in a password manager for later approved schema
work. The restricted `momentum_app` role and its distinct pooled `DATABASE_URL`
are created only in the approved schema phase. Keep every staging value separate
from development and production, including the future Neon Auth issuer/JWKS and
user data. No application migrations or seed data are applied at this checkpoint.

## Later steps requiring separate approval

1. Review the staged schema plan separately before authorizing SQL. Start with a
   catalog check, provision the restricted `momentum_app` login, then use the
   [migration record](../backend/migrations/README.md) for 001–014 and the base
   grants. A clean target uses 010 followed later by 014. The combined 010/014
   shape is historical development recovery. Stop on errors and verify each
   committed checkpoint. Use a Console-issued direct admin connection for
   reviewed schema work and a separate pooled restricted URL for normal traffic.
   Run `python -m app.schema_audit` and selected two-tenant rollback-only tests
   before exposing synthetic app traffic.
2. Review the exact Git revision and authorize sharing it with the host. Create
   the Render services using `render.staging.yaml` as a custom Blueprint on that
   revision's staging branch. Validate the plan and confirm charges before sync.
   Auto-deploy is off, so manually select and record each deployed revision.
   The Blueprint creates neither a database nor a scheduler and has no migration hook.
3. Set the approved staging Auth base and JWKS URLs on the API. Build the UI with
   the same branch's public `/auth` URL. Register the exact deployed HTTPS origin
   in Neon Auth and verify the issuer/key setup with a synthetic sign-in. Leave
   Google disabled in the UI and keep optional provider flows disabled at the
   provider until verified. Keep support and AI configuration optional for the
   first infrastructure smoke test. Add an approved staging Gemini key and model
   before an AI demo.
4. Share the HTTPS URL only with demo reviewers until launch gates clear. Use
   disposable, separate synthetic identities for tenant tests. Deliver demo access
   privately and set a cleanup date. A public landing URL by itself does not make
   any account or workspace public.

## Environment values

| Scope | Values |
| --- | --- |
| Public web build | `VITE_NEON_AUTH_URL`, optional public `VITE_SUPPORT_EMAIL`, and `VITE_GOOGLE_SIGN_IN_ENABLED=false`. Use a stable canonical HTTPS origin for demo and push. |
| Web runtime | `PORT=8080` and Blueprint-managed `MOMENTUM_API_UPSTREAM` from the private service's `hostport`. Requests to `/api/v1/*` stay same-origin. Browser CORS allowlists require no change. The frontend terminates TLS at Render's edge; the internal proxy hop uses HTTP on the private network. |
| FastAPI | `NEON_AUTH_BASE_URL`, `NEON_AUTH_JWKS_URL`, restricted staging `DATABASE_URL`, optional `GEMINI_API_KEY` and `GEMINI_MODEL`. Use the host's protected variables. Never declare secret values as Docker `ARG`s or print them. |
| API and future Cron | Optional staging `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` on the server-side services that send push. Keep the same staging keypair across revisions and separate from other environments. Browsers fetch only the public key and create fresh subscriptions under the exact staging origin. |
| Cron only, deferred | `REMINDER_DATABASE_URL`, a separate restricted login inheriting `momentum_scheduler`. Leave Cron unprovisioned until worker authentication and grants are verified independently. |

Record the actual platform and browser observations. Check TLS and `/health/live`
through the public frontend. Verify internal `/health/ready` from the private
network (for example, from a Render Shell on the staging API) and confirm the
public `/health/ready` returns 404. Render checks the private service using TCP;
run the application readiness check separately before sharing the demo. Frequent readiness
probes query Neon and can defeat scale-to-zero, so use readiness for rollout and
incident checks. Check that protected API calls require a session. Verify Neon
origins, referrers and ingress logs with synthetic data before enabling reset
flows. Nginx's current rate limit keys on the immediate peer. Verify the provider's
trusted proxy chain and load behavior before depending on per-client limits.
[Render health checks](https://render.com/docs/health-checks)

## Smoke test and rollback

- Verify synthetic sign-in, Overview, create/approve a task, saved chat reload,
  opportunity browse and sign-out over the staging HTTPS URL. Use two identities
  to check isolation. Verify API errors and public health responses contain no
  account data. Record the exact revision and checks in the release log.
- If push is enabled, verify permission and direct device delivery separately.
  After the worker gate clears, check quiet hours, closed-tab delivery, restart
  recovery and duplicates. Then verify the inbox and actual device receipt.
- Keep a known-good frontend/API revision pair. On regression disable publicity
  and pause any worker, then use Render's deployment rollback or rebuild the
  approved pair and rerun the smoke tests. Keep compatible additive schema and
  existing data in place. Restore into a separate staging branch for rehearsal
  and reconcile writes before any restore is considered for a live environment.
  [Render rollbacks](https://render.com/docs/rollbacks)

## Submission checklist

- [ ] Record the HTTPS demo URL and confirm `/health/live` and internal readiness.
- [ ] Supply synthetic demo account access privately and verify the guided journey.
- [ ] Verify README setup, deployed revision and staging rollback instructions.
- [ ] Capture desktop/mobile screenshots and a short walkthrough with synthetic data.
- [ ] Include reviewed privacy/security disclosures, AI processing and optional push.
- [ ] State known limitations and which features are disabled in the demo.
- [ ] Record approved rollback owner, target revision and recovery test evidence.

## Gates before public launch

- Verify whether Neon managed Auth is patched or outside the affected OAuth/Magic
  Link and OAuth Proxy configurations. Contact the provider with the advisory IDs
  and staging Auth service metadata only. See the [security review](security-review.md).
- Restricted scheduler authentication remains blocked. Scheduled external delivery
  and restart recovery remain unverified. Prior Windows direct push was verified.
- Full tenant isolation remains incomplete across private tables and APIs.
- Full account deletion is incomplete. Approve retention for workspace, provider,
  audit and backups. Verify synthetic recovery email, expiration, branch restore
  and app rollback. Follow the [release checklist](release-checklist.md).

**Next checkpoint:** verify the new project and branch identifiers and review the
schema and role plan. Render pricing and provisioning require separate approval.
