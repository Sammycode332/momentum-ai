# Momentum AI scope audit

The [master specification](master-specification.md) controls release scope. The
[release plan](release-plan.md) defines acceptance gates. The last verified
development recovery passed 107 backend and 45 frontend tests, including real
PostgreSQL isolation for goals and conversations. Signed synthetic API requests
covered identity, onboarding, dashboard data and conversation history. This
evidence was recorded before the signed-in workflows below were verified.

## Phase 9 checkpoint

- **Verified in a browser by the owner:** signed-in workspace retrieval, task creation and edits, goal creation, selective roadmap persistence across Goals, Projects and Tasks, and direct Windows push. The owner also verified public opportunity listings and external links while signed out. Development PostgreSQL tests exercise signed-in persistence paths with synthetic owners and rolled-back records.
- **Implemented with browser checks pending:** OTP and password recovery, configured Google sign-in, approved memory, practice and interviews, account export, and desktop/mobile PWA installation. The owner verified fresh sign-in, Overview cold reload and sign-out.
- **Security and reliability:** reads now attempt one uncached same-account refresh on recognized token rejection. The API screens unusable JWT claims before looking up signing keys and still verifies signatures. Cross-user API verification across all private domains and complete dependency advisory review remain open.
- **Accessibility and performance:** automated build and lint cover source checks. Browser keyboard, focus, contrast and responsive review, database query and request latency under representative workloads, and container execution measurements remain open.
- **Operations:** private API liveness and database/RLS readiness are available. Staging topology, HTTPS and exact Auth origins, environment secrets, dependency/image pinning, alerts, and backup/rollback rehearsals remain release gates. Full account deletion and retention policy also need closure.
- **Scheduled delivery blocker:** the last restricted development scheduler authentication check failed. Closed-tab scheduled Windows delivery and restart recovery are pending. Scheduler password troubleshooting is paused.

## A. Product requirements

| Section | Status | Evidence and remaining work |
| --- | --- | --- |
| 1. Repository discovery | Verified complete for this checkpoint | Existing Git history, architecture, tests, runtime role, and migration state are documented. Refresh when they change. |
| 2. Computer verification | Partial | Terminal and real development database checks passed. Signed-in browser Network, responsive and screenshot evidence remain open. |
| 3. Product vision | Partial | Connected workspace and general-purpose assistant exist. Validate full workflows across different user types. |
| 4. Design and UX | Implemented but unverified in browser | Shared themes, navigation, landing, forms and Assistant modes exist. Review both themes, keyboard and mobile layouts in a real browser. |
| 5. Authentication | Core session lifecycle user-verified | Fresh sign-in, Overview cold reload and sign-out passed in the owner's browser. Provider recovery and optional flows, branch association and hosted advisory status still need release evidence. |
| 6. Dashboard and productivity | Partial | Records, linked tasks, milestones, goals, application stages, reminders and dashboard reads work at the API level. Verify editing/filtering workflows and recommendation coverage. |
| 7. AI assistant | Partial | Gemini adapter, bounded context, persistence, rename/delete, Markdown and retry exist. Live multi-turn and cancellation checks remain. Streaming is deferred under ADR-021. |
| 8. Tutoring | Implemented but unverified live | Guided topics, questions, feedback, progression limits and session history exist. Evaluate a live learning path and saved answers. |
| 9. Interview preparation | Implemented but unverified live | Role/format selection, rubric, feedback and saved sessions exist. Evaluate mock interviews and follow-up quality. |
| 10. Opportunity discovery | Partial | Owner verified public browsing, visible listings and external application links. Verify freshness, stale-feed handling and the signed-in save workflow separately. Other requested categories need legitimate sources. |
| 11. Personalized memory | Implemented but unverified live | Proposal, approval, correction, deletion and bounded retrieval exist. Verify cross-user isolation and relevance in live conversations. |
| 12. Reminders and notifications | Partial and externally blocked | Scheduling, quiet hours, check-ins, snooze, history, push, retries and PWA shell exist. Verify worker and device delivery, linked-deadline behavior and supported installation. Optional email is missing. |
| 13. Controlled actions | Implemented but unverified live | Structured proposals, separate approval, audit, idempotency and guarded deadline undo exist. Verify live execution, stale-target conflicts and cross-user denial. |
| 14. Security and backend quality | Partial | JWT guards, restricted roles, active RLS, request and AI limits and sanitized errors exist. Full endpoint isolation, dependency review, pagination and operational observability remain open. |
| 15. Performance and accessibility | Partial | Lazy routes, bounded requests and reduced-motion/keyboard foundations exist. Measure browser performance, contrast, focus, responsive behavior and screen-reader interaction. |
| 16. Testing and QA | Partial | Backend/frontend suites and two live SQL isolation tests passed. Real browser workflows, broader cross-user cases and provider/device evidence remain open. |
| 17. Deployment and release engineering | Partial | Container and CI templates, liveness, migration instructions and runbook exist. Validate containers, worker hosting, monitoring, backups and rollback in staging. |
| 18. Market readiness | Partial | Landing, onboarding, export and configurable support exist. Terms/privacy drafts need review. Full account deletion and feedback workflow need completion. |
| 19. Implementation strategy | Verified complete as a planning deliverable | Original phase definitions and acceptance gates are preserved. Execution remains open. |
| 20. Git and delivery | Partial | No commits or pushes in this audit. Release review and delivery approvals remain open. |
| 21. Final deliverables | Partial | Architecture, migration record, test evidence, security checkpoint, deployment guide and checklist exist. Browser evidence and verified release readiness remain open. |
| 22. Start and execution | In progress | Repository and evidence reviewed. Next gate is live authentication verification. |

## B. Implementation roadmap

| Phase | Implemented and verified so far | Open gate and next action |
| --- | --- | --- |
| 0 | Inventory, architecture, bug register, release plan, live schema audit | Finish dependency review and refresh release evidence. |
| 1 | Restricted runtime recovery, signed-in cold reload, passing automated auth tests and persisted conversation isolation | Confirm Neon Auth branch ownership and verify recovery and optional provider flows. |
| 2 | Unified Assistant, shared themes and navigation, auth screens | Review desktop, tablet and mobile in browser, including focus and contrast. |
| 3 | Private record reads verified against Neon, CRUD and relationships implemented | Exercise goal/project/task and application-stage create/edit paths with synthetic data. |
| 4 | Persistent chat and memory approval controls implemented | Verify live multi-turn Gemini, approved-memory retrieval, corrections and tenant boundaries. |
| 5 | Guided tutoring and interview practice implemented | Evaluate real sessions and saved progress with controlled prompts. |
| 6 | Public listings and external destinations user-verified; private saves implemented | Verify freshness, unavailable-source behavior and signed-in saving. Obtain authorized sources for missing categories. |
| 7 | Reminder storage and RLS verified with synthetic fixtures. Owner verified direct Windows push. | Restricted worker authentication blocks the scheduled closed-tab and restart tests. PWA installation remains unverified. |
| 8 | Approval workflow, history and guarded undo implemented. 010/014 schema verified | Test approved/rejected/reverted actions and concurrent edits in development. |
| 9 | Export, liveness and database readiness, user-verified cold reload, Zod remediation, export isolation integration, CI/container templates and operational drafts | Confirm Neon-managed Auth advisory status, broaden tenant isolation checks, then validate staging, recovery, accessibility, retention, account deletion and cost controls. |

Existing additions beyond the detailed master examples include safe deadline
undo, bulk read/dismiss controls, and the explicit application-stage pipeline.
They extend approval recovery, notifications and application tracking without
replacing those requirements. Account export is a concrete data-handling
control under section 18. Attribution to a specific agent is based on the
project progress records rather than Git authorship of uncommitted files.

## Development database checkpoint

The earlier recovery instruction in the scope correction predates the approved
repair. On the verified replacement branch, 001–004, 008 and 013 were preserved.
Base grants, 005–007, corrected 009, 010 with 014 incorporated, and 011–012 were
committed and checked through fresh connections. `momentum_app` is restricted,
`momentum_scheduler` is `NOLOGIN`, and the runtime schema audit confirmed active
RLS on 20 owned tables. The [migration runbook](../backend/migrations/README.md)
records the sequence. No SQL repair is indicated by the last checkpoint. Any
new discrepancy requires a read-only check and an approved repair plan.

## Latest local verification

The production frontend build passed. The existing local frontend returned HTTP
200 and its unsigned API request returned 401. An isolated API also returned
200 for liveness and 401 for an unsigned protected request. Browser inspection
of the local Chrome app window timed out before returning page state. No live
session, signed-in cold reload, responsive review, or screenshot was verified.
Continue BUG-001 on the confirmed development Auth endpoint with a synthetic
sign-in and capture only response statuses and sanitized request references.
