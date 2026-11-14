# Implementation Backlog

## Master mission checkpoint — 2026-11-13

- RC-FEATURES (in progress): memory approval/personalization, persistent tutoring/interviews, approved actions, reminders/worker, legitimate discovery, core linking and release UX/operations. Acceptance: real API-connected screens, owner-isolated storage, bounded provider calls, approval enforcement, focused regression checks and production build. External activation and browser evidence remain separate from implementation status.

- CORE-03 (in progress; implementation and automated checks pass): goal edit/complete/reopen/delete, search/filter and truthful completion counts. API tests cover ownership and validation; UI tests cover workflow, cancellation and failed-save drafts. Migration 005 application, isolated SQL test and live browser verification remain open (BLK-RC-04).

- RC-00 (in progress): repository audit, [feature inventory and release gates](release-plan.md), [bug register](bugs.md), baseline tests and read-only schema audit. Full dependency/security audit remains open.
- RC-01 (in progress): investigate first-load rejection using signed-in browser and sanitized verifier diagnostics. Browser showed a rejection and later a loaded Overview; no root-cause claim. Future-dated JWTs now have a distinct rejection code without changing acceptance rules.
- RC-02 (implemented; browser verification incomplete): recoverable sign-out errors, safe initial session error mapping, bounded record descriptions and null-text validation, on-demand assistant loading, removal of unsupported system-health claim. Automated results in progress.md.
- Next: finish authenticated cold-load Network/log correlation, then run controlled two-user PostgreSQL and API CRUD isolation checks before advancing the design phase.

Status values: proposed, ready, in progress, blocked, complete. Use `proposed` for unstarted work. Use `blocked` only when a specific open `BLK-` entry prevents work.

## Phase 0 — Foundation

| ID | Description | Dependencies | Acceptance criteria | Priority | Status |
| --- | --- | --- | --- | --- | --- |
| FND-01 | Bootstrap the minimum React + TypeScript + Vite + Tailwind CSS v4 frontend in `frontend/` and Python + FastAPI backend in `backend/` | ADR-002; ADR-008; ADR-009; ADR-010 | Both minimal scaffolds follow ADR-009 and ADR-010; frontend install, development, build, and lint commands plus backend installation, startup, and import/startup verification commands are documented | P0 | complete |
| FND-02 | Establish environment, configuration, and secrets conventions | FND-01 | No secrets committed; local/staging configuration approach documented | P0 | complete |
| FND-03 | Establish test tooling and controlled fixtures | FND-01 | Unit/integration test commands run; fixture policy supports isolated user and privileged-access tests | P0 | complete |
| FND-04 | Define minimal online MVP deployment baseline | FND-02; ADR-006; BLK-04 | Provider-agnostic deployment, migration, configuration, and rollback procedure documented; no provider is selected implicitly | P0 | blocked |
| FND-05 | Define API versioning and error conventions | FND-01; ADR-007 | Versioning and error convention recorded before private API endpoints are exposed | P0 | complete |

FND-01 completed at `dcfd151` after the documented frontend and backend checks. FND-02 completed after verification of its ignore rules, trackable templates, and configuration convention. FND-05 completed with the accepted API versioning and safe error-response convention in ADR-007; no private endpoints have been exposed. FND-03 completed after frontend and backend test commands passed and its controlled-fixture policy was documented. See [progress](progress.md) for the results.

## Phase 1 — Identity and data isolation

| ID | Description | Dependencies | Acceptance criteria | Priority | Status |
| --- | --- | --- | --- | --- | --- |
| ID-01 | Integrate Neon Auth and backend credential verification | FND-01, FND-02, FND-05 | Private API rejects missing/invalid credentials and exposes verified identity to services | P0 | complete |
| ID-02 | Design initial user-owned schema and RLS policies | ID-01, FND-03 | Owner-scoped records and policies exist; user-scoped and service-role access paths both reject cross-user reads/writes | P0 | in progress |
| ID-03 | Create onboarding profile/context flow | ID-02 database foundation for implementation; ID-02 isolation verification for closure | Authenticated users can complete or skip short onboarding and later view and edit their private, validated preferences | P0 | in progress |

## Phase 2 — Core user experience

| ID | Description | Dependencies | Acceptance criteria | Priority | Status |
| --- | --- | --- | --- | --- | --- |
| CORE-01 | Implement core records for projects, tasks, learning, academics, and opportunities | ID-02 | A user can manage their own essential records across all five domains; ownership and validation tests pass | P0 | in progress |
| CORE-02 | Implement personalized dashboard | ID-03, CORE-01 | Dashboard uses only the current user’s records and presents prioritized core context | P0 | in progress |

## Phase 3 — AI assistance and controlled changes

| ID | Description | Dependencies | Acceptance criteria | Priority | Status |
| --- | --- | --- | --- | --- | --- |
| AI-01 | Implement read-only Gemini chat and structured planning | CORE-01, ADR-004, ADR-019, ADR-020 | Authorized context and explicit history support chat, structured planning remains validated, and a live authenticated check succeeds | P0 | in progress |
| AI-02 | Implement memory proposal and approval workflow | AI-01, ID-02 | Memory changes remain pending until explicit approval; approvals/actions are auditable | P0 | proposed |
| AI-03 | Define and implement bounded routine task reprioritization and rescheduling | CORE-01, AI-01; BLK-03 | Routine changes follow defined permissions; consequential changes are approval-gated; all actions are auditable and recoverable | P0 | blocked |

## Phase 4 — Evaluation and release readiness

| ID | Description | Dependencies | Acceptance criteria | Priority | Status |
| --- | --- | --- | --- | --- | --- |
| REL-01 | Implement initial AI evaluation suite | AI-01, AI-02, AI-03; BLK-06 | Five required scenarios run with critical safety gates; critical failures block release | P0 | blocked |
| REL-02 | Define production-hardening and release operations, then validate production security | FND-04, ADR-006; BLK-04, BLK-05 | Monitoring, incident handling, costs, retention, secrets, rollback, and production-security procedures are documented and validated | P0 | blocked |


- UI-CONSOLIDATE (implemented; visual verification blocked): owner's requested unified Assistant modes and reduced navigation. Acceptance: no standalone learning studio/interview/approval/discovery/memory sidebar destinations; capabilities remain reachable in the appropriate hub; drafts preserved across mode switches; production build and lint pass. ADR-026 records the decision. Browser preview timed out; screenshot and responsive approval remain open.
- RC-FEATURES: code added across later phases; no phase is closed by code presence. See current inventory in release-plan.md. Prioritize frontend review next per owner steering.

- ACCOUNT-EXPORT (in progress): Settings export with bounded owner-scoped pages, no secret fields, explicit incomplete/export-failure handling and a support link from configured contact only. Verify owner scoping and unknown sections; build frontend. Full account deletion remains separate.
- RELEASE-BASELINE (in progress): container, CI, setup and operator runbook templates; no deployment. Validate config/build where local tooling permits; report untested container/runtime assumptions.

- ACCOUNT-EXPORT: implemented; 13 account/auth checks and frontend build/lint pass. Live export unverified. Full account deletion remains separate.
- RELEASE-BASELINE: Docker/proxy/CI and runbook/checklist/security drafts prepared. Container execution blocked by unavailable Docker engine; remote CI, rollout/rollback and backup rehearsal unverified.
- AUTH-RECOVERY: provider-managed recovery plus gated Google UI implemented. Two mocked recovery tests/build/lint pass; provider email/OAuth activation and browser verification pending.

- PRODUCTIVITY-CONNECT: record reminder composer, project task/milestone view, opportunity pipeline/filter, Overview goal/reminder panels implemented. Migration 013 prepared; live verification pending. Broad suites deferred as requested.
- CHAT-CONNECT: response-to-memory/action proposal controls implemented; separate approval preserved; default prompts no longer assume engineering roles. Build/import checks only at this stage.
- CHAT-TASK: user-verified in a signed-in browser. Automated coverage verifies that approval inserts once, while rejection and failed writes leave Tasks unchanged.
- CHAT-WORKSPACE: all five read views and tenant isolation verified with authenticated API and restricted PostgreSQL fixtures. The owner verified real workspace retrieval in a signed-in browser.
- CHAT-TASK-EDIT: single-field task changes implemented in chat and Approvals. Automated checks cover matching, ambiguity, approval, rejection, idempotency, stale edits, and rollback. The owner verified approval and persistence in a signed-in browser.
- CHAT-GOAL-PLAN: goal and selective roadmap approval verified in automated and restricted PostgreSQL tests. Verify the signed-in chat review, resulting records after page reload, and saved progress.

- NOTIFICATION-UX: morning/evening daily reminder shortcuts, unread/read/dismissed filters, bounded visible-record read/dismiss controls, reminder status filter and upcoming-first ordering implemented. Build/import checks in progress; live delivery/persistence still gated by runtime DB credentials and worker activation.
