# Release candidate mission — 2026-11-13

Scope is defined by the [22-section master specification](master-specification.md).
See the [coverage and roadmap audit](scope-audit.md) for the current status of
each requirement and Phase 0–9. The five-phase overview is for reporting only.

## Current increment

Owner approved independent implementation while the authentication/browser blocker is deferred, then explicitly prioritized frontend consolidation. Current UI uses a single AI Assistant with Chat/Learn/Interview/Approvals modes, Opportunities with Saved/Discover views, and Settings with profile/memory controls. Build and lint pass; final browser review is blocked. The initial inventory below is historical, not current implementation status.

### Current feature classification

| Feature | Status and evidence |
| --- | --- |
| Existing auth/onboarding/dashboard/CRUD/chat | Implemented; existing automated coverage; cold-load root cause and live multi-user verification still open |
| Goal lifecycle and task relationships | Implemented, build/API validation checked; new schema and real linked workflows not verified |
| Consolidated frontend, landing, filters | Implemented and build/lint verified; screenshot/responsive/accessibility review incomplete |
| Approved memory, tutoring/interview sessions, controlled actions | Implemented, focused safety tests passed; live persistence/RLS/provider evaluation incomplete |
| Remotive opportunity discovery | Implemented public source adapter/cache/attribution; live feed not exercised; jobs/internships only |
| Reminders and push | Durable scheduling/subscriptions/retries code present; helper tests passed; worker hosting/VAPID/device delivery blocked by external setup |
| PWA | Minimal manifest/service worker prepared; installation and iOS icon/device support not verified |
| Streaming | Deferred under ADR-021; atomic replies remain |
| Account export and support | Implemented Settings UI and owner-scoped paged API; focused backend tests/build pass; live export unverified; support address configurable |
| Password recovery and Google OAuth | Recovery implemented with 2 mocked flow tests; Google UI gated by operator configuration; live provider verification pending |
| Full account deletion and final privacy/terms | Deletion unfinished; internal privacy/terms draft prepared for operator/legal review |
| Deployment/CI/operations | Docker/proxy/CI templates, setup/runbook/checklist prepared; containers and remote CI untested; backup/rollback rehearsal and security audit pending |

No phase is fully closed by these code changes. The preliminary audit exists; its full dependency-security audit is also unfinished. Latest evidence and limitations are in progress.md and testing.md.

The owner's master mission expands the earlier MVP. Preserve the existing stack and uncommitted work. No production deployment, paid service, destructive migration, or push is authorized. A passing mock test is not live verification.

## Acceptance gates

| Phase | Scope | Required evidence before closure |
| --- | --- | --- |
| 0 | Inventory, bug register, architecture and dependency audit | Code-backed inventory, baseline checks, safe migration inspection |
| 1 | Session restoration, chat reliability, security defects | Signed-in cold reload/network diagnosis, regression tests, two-user database isolation, saved-turn retry |
| 2 | Shared visual system and responsive screens | Desktop/tablet/mobile screenshots, both themes, keyboard and reduced-motion checks |
| 3 | Core productivity | Create/edit/complete/link/search workflows and failure recovery using synthetic records |
| 4 | Chat and approved memory | Bounded context, explicit approval, audit, correction/deletion, tenant tests |
| 5 | Tutoring and interviews | Persistent sessions, exercises/evaluation, rubrics, progress without invented mastery |
| 6 | External opportunities | Authorized source adapter, real URLs, freshness/deduplication; costs require approval |
| 7 | Reminders/PWA | Durable scheduling decision, timezone/quiet-hours/idempotency tests, supported-device delivery |
| 8 | AI actions | Structured proposals, explicit approval, authorization, audit/recovery tests |
| 9 | Release operations | Deployment/rollback rehearsal, security/accessibility/performance evidence, retention and cost decisions |

Phase numbers here refer to the master mission, not the older backlog. Advance only after relevant gates; record external blockers without claiming completion.

## Initial code-backed inventory

- Implemented, automated tests available, live verification incomplete: email/password and OTP auth, session restoration, onboarding, dashboard, five-domain CRUD, Gemini chat/planning, persisted conversations, rename/delete/retry, safe Markdown, light/dark themes.
- Goals currently support create/list only; goal editing, milestones, subtasks and goal/task linkage are missing.
- Missing: approved long-term memory, dedicated tutoring/interviews, live opportunity discovery, durable reminders/push/PWA, controlled AI actions, account deletion/export and production operations.
- Conversation lists/display are bounded but lack pagination; record lists are unbounded. Generation holds a conversation database row lock while calling Gemini. Cancellation does not cancel backend generation. Streaming is deliberately deferred under ADR-021.
- No backend README or root setup README existed at audit start. Frontend README was scaffold text. No CI/deployment definitions were found in the initial inventory.
- Migrations 001–004 are present; do not rerun them to determine status. Inspect catalog metadata using the configured role without reading user rows.

## Baseline evidence

- Frontend: 37 tests pass; lint passes; build passes, with a 533.71 kB initial JS chunk warning.
- Backend: 54 tests pass, 2 isolated PostgreSQL checks skipped. Existing Python 3.13 virtual environment works outside the execution sandbox; sandbox cannot launch it.
- Windows browser inventory found the frontend Chrome window, but accessibility was unavailable and screenshot capture timed out. No browser workflow has been verified in this audit yet.
- Working tree was already extensively modified/untracked before this mission. Do not attribute all current diffs to this mission or commit them indiscriminately.
