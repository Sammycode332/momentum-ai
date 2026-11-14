# Blockers and Open Questions

2026-11-14 update. Restricted database connectivity and the missing development
migrations are repaired. Earlier credential and missing-role entries below are
historical for this branch. Neon Auth branch ownership and live sign-in still
require confirmation. The scheduler group exists; worker activation is separate.

## Release mission blockers — 2026-11-13

- BLK-RC-04: CORE-03 code requires additive migration 005 and its isolated PostgreSQL test. Configured `momentum_app` is deliberately restricted and is not a schema-owner connection. Migration is prepared and documented, not applied; activate the new backend only after the schema-owner workflow succeeds. No new production or credential access is assumed.

- BLK-RC-01: Computer Use stopped the browser test because it could not confidently determine the current URL. No further UI actions were taken. A fresh browser-tool session is needed to finish cold-load and Network verification. User authorized the signed-in development session for synthetic tests.
- BLK-RC-02: Isolated PostgreSQL test URLs are not configured, so two existing integration checks skip. Catalog inspection confirms active forced RLS and restricted runtime role but does not prove cross-user CRUD isolation.
- BLK-RC-03: Hosting/worker, external opportunity source, notification delivery, production retention/provider terms and budgets remain unselected. Do not create paid resources or deploy based on assumptions.

Resolved entries remain in this file with their history.

| ID | Type | Blocker / question | Impact | Possible resolution | Status |
| --- | --- | --- | --- | --- | --- |
| BLK-01 | Decision | Frontend and backend bootstrap details were open under the monorepo layout accepted in ADR-009 | Blocked FND-01 scaffold and local development setup | Resolved by ADR-010: per-application React + TypeScript + Vite + Tailwind CSS v4 and FastAPI bootstraps with documented local verification; no root orchestration tooling, backend test framework, or custom application endpoints | resolved |
| BLK-02 | Requirement | Onboarding fields and initial dashboard composition were unspecified | Previously blocked CORE-02 | ADR-016 defines onboarding fields. The CORE-02 brief and ADR-018 define the initial dashboard. | resolved |
| BLK-03 | Security/product | Boundaries and defaults for routine reprioritization/rescheduling are undefined | Unsafe or surprising agent actions; blocks AI-03 | Define consent, routine versus consequential changes, limits, approval gates, audit, reversal, and failure handling | open |
| BLK-04 | Infrastructure | Hosting, environments, scheduling, monitoring, migrations, and cost limits are undecided | Blocks selecting a minimal online MVP deployment baseline and production operations | ADR-019 selects Gemini for planning. Select remaining services deliberately and update ADR-006. | open |
| BLK-05 | Data/security | Data retention/deletion expectations and AI-provider data handling terms are unknown | Cannot finalize privacy controls or logging policy | Confirm policy and provider agreement before handling production data | open |
| BLK-06 | Quality | Success metrics and test data for AI recommendations are unselected | Evaluation pass/fail thresholds cannot be finalized | Define scenario fixtures, expected outcomes, and critical safety criteria | open |


- 2026-11-13 update: browser tool can inventory Windows apps but opening localhost:5173 in its in-app browser timed out. No browser screenshot claim.
- New feature activation needs schema-owner application/verification of 005–012, dedicated worker login/hosting, optional push package and VAPID configuration. User reported 009 missing scheduler role; corrected migration now creates restricted NOLOGIN role and has recovery steps. Successful retry has not been reported. Never rerun already successful migrations.

- 2026-11-14: Docker CLI exists but Docker Desktop Linux engine pipe is unavailable; container configuration remains unexecuted. Read-only Neon schema audit could not connect; current migration application state remains unknown. Password recovery delivery/Google OAuth need synthetic provider verification; full account erasure needs identity/retention coordination. Usage-limit approval failure from the prior turn no longer blocks editing.

- 2026-11-14 onboarding 503 narrowed to runtime DB authentication rejection (safe diagnostic category DB_CREDENTIALS; momentum_app). Tool configuration source is backend/.env. Requires valid runtime URI/password for intended branch; no permission weakening or schema rerun is appropriate for this failure. Migration 013 is prepared but not applied.

Notification UI/bulk-state work adds no migration and does not resolve the existing runtime credential rejection. No live notification data or external delivery was exercised.

- Milestone C still needs a signed-in browser walkthrough. Goal description and target date on the Goals page would require a separately approved schema change. The proposal history already retains these details.
