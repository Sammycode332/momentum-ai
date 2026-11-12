# Implementation Backlog

Status values: proposed, ready, in progress, blocked, complete. No implementation task has started.

## Phase 0 — Foundation

| ID | Description | Dependencies | Acceptance criteria | Priority | Status |
| --- | --- | --- | --- | --- | --- |
| FND-01 | Select frontend framework and repository layout | ADR-002 approval | Decision recorded; minimal project structure and local run/test commands documented | P0 | blocked |
| FND-02 | Establish environment, configuration, and secrets conventions | FND-01; hosting decisions | No secrets committed; local/staging configuration approach documented | P0 | blocked |
| FND-03 | Establish test tooling and controlled fixtures | FND-01 | Unit/integration test commands run; fixture policy supports isolated user tests | P0 | blocked |

## Phase 1 — Identity and data isolation

| ID | Description | Dependencies | Acceptance criteria | Priority | Status |
| ID-01 | Integrate Supabase Auth and backend credential verification | FND-01, FND-02 | Private API rejects missing/invalid credentials and exposes verified identity to services | P0 | blocked |
| ID-02 | Design initial user-owned schema and RLS policies | ID-01 | Owner-scoped records and policies exist; cross-user read/write tests fail safely | P0 | blocked |
| ID-03 | Create onboarding profile/context flow | ID-02 | Authenticated user can complete short onboarding; records are private and validated | P0 | blocked |

## Phase 2 — Core user experience

| ID | Description | Dependencies | Acceptance criteria | Priority | Status |
| CORE-01 | Implement core records for projects, tasks, learning, academics, and opportunities | ID-02 | A user can manage their own essential records; ownership and validation tests pass | P0 | blocked |
| CORE-02 | Implement personalized dashboard | ID-03, CORE-01 | Dashboard uses only the current user’s records and presents prioritized core context | P0 | blocked |

## Phase 3 — AI assistance and controlled changes

| ID | Description | Dependencies | Acceptance criteria | Priority | Status |
| AI-01 | Define/implement hosted AI provider interface and planning endpoint | CORE-01, ADR-004 | Authorized minimal context produces validated plan/recommendation output; provider can be substituted in tests | P0 | blocked |
| AI-02 | Implement memory proposal and approval workflow | AI-01, ID-02 | Memory changes remain pending until explicit approval; approvals/actions are auditable | P0 | blocked |
| AI-03 | Define and implement bounded task reprioritization/rescheduling | CORE-01, AI-01; autonomy policy decision | Only allowed routine actions occur; actions are auditable and recoverable | P0 | blocked |

## Phase 4 — Evaluation and release readiness

| ID | Description | Dependencies | Acceptance criteria | Priority | Status |
| REL-01 | Implement initial AI evaluation suite | AI-01 through AI-03 | Five required scenarios run with safety gates; failures block release | P0 | blocked |
| REL-02 | Select deployment/operations and validate production security | FND-02, ADR-006 | Hosting, migrations, monitoring, costs, secrets, and rollback procedures are documented and tested | P0 | blocked |
