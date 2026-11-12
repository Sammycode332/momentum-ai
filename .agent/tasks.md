# Implementation Backlog

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
| ID-01 | Integrate Supabase Auth and backend credential verification | FND-01, FND-02, FND-05 | Private API rejects missing/invalid credentials and exposes verified identity to services | P0 | proposed |
| ID-02 | Design initial user-owned schema and RLS policies | ID-01, FND-03 | Owner-scoped records and policies exist; user-scoped and service-role access paths both reject cross-user reads/writes | P0 | proposed |
| ID-03 | Create onboarding profile/context flow | ID-02; BLK-02 | Authenticated user can complete short onboarding; records are private and validated | P0 | blocked |

## Phase 2 — Core user experience

| ID | Description | Dependencies | Acceptance criteria | Priority | Status |
| --- | --- | --- | --- | --- | --- |
| CORE-01 | Implement core records for projects, tasks, learning, academics, and opportunities | ID-02 | A user can manage their own essential records across all five domains; ownership and validation tests pass | P0 | proposed |
| CORE-02 | Implement personalized dashboard | ID-03, CORE-01; BLK-02 | Dashboard uses only the current user’s records and presents prioritized core context | P0 | blocked |

## Phase 3 — AI assistance and controlled changes

| ID | Description | Dependencies | Acceptance criteria | Priority | Status |
| --- | --- | --- | --- | --- | --- |
| AI-01 | Define/implement hosted AI provider interface and planning endpoint | CORE-01, ADR-004; BLK-04 | Authorized minimal context produces validated plan/recommendation output; provider can be substituted in tests | P0 | blocked |
| AI-02 | Implement memory proposal and approval workflow | AI-01, ID-02 | Memory changes remain pending until explicit approval; approvals/actions are auditable | P0 | proposed |
| AI-03 | Define and implement bounded routine task reprioritization and rescheduling | CORE-01, AI-01; BLK-03 | Routine changes follow defined permissions; consequential changes are approval-gated; all actions are auditable and recoverable | P0 | blocked |

## Phase 4 — Evaluation and release readiness

| ID | Description | Dependencies | Acceptance criteria | Priority | Status |
| --- | --- | --- | --- | --- | --- |
| REL-01 | Implement initial AI evaluation suite | AI-01, AI-02, AI-03; BLK-06 | Five required scenarios run with critical safety gates; critical failures block release | P0 | blocked |
| REL-02 | Define production-hardening and release operations, then validate production security | FND-04, ADR-006; BLK-04, BLK-05 | Monitoring, incident handling, costs, retention, secrets, rollback, and production-security procedures are documented and validated | P0 | blocked |
