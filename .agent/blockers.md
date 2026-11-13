# Blockers and Open Questions

Resolved entries remain in this file with their history.

| ID | Type | Blocker / question | Impact | Possible resolution | Status |
| --- | --- | --- | --- | --- | --- |
| BLK-01 | Decision | Frontend and backend bootstrap details were open under the monorepo layout accepted in ADR-009 | Blocked FND-01 scaffold and local development setup | Resolved by ADR-010: per-application React + TypeScript + Vite + Tailwind CSS v4 and FastAPI bootstraps with documented local verification; no root orchestration tooling, backend test framework, or custom application endpoints | resolved |
| BLK-02 | Requirement | Onboarding fields and initial dashboard composition were unspecified | Dashboard composition still blocks CORE-02 | ADR-016 resolves onboarding fields. Confirm initial dashboard priorities separately. | open for CORE-02 |
| BLK-03 | Security/product | Boundaries and defaults for routine reprioritization/rescheduling are undefined | Unsafe or surprising agent actions; blocks AI-03 | Define consent, routine versus consequential changes, limits, approval gates, audit, reversal, and failure handling | open |
| BLK-04 | Infrastructure | AI provider, hosting, environments, scheduling, monitoring, migrations, and cost limits are undecided | Blocks selecting a minimal online MVP deployment baseline and production operations | Select services deliberately; distinguish MVP deployment from later hardening; update ADR-006 | open |
| BLK-05 | Data/security | Data retention/deletion expectations and AI-provider data handling terms are unknown | Cannot finalize privacy controls or logging policy | Confirm policy and provider agreement before handling production data | open |
| BLK-06 | Quality | Success metrics and test data for AI recommendations are unselected | Evaluation pass/fail thresholds cannot be finalized | Define scenario fixtures, expected outcomes, and critical safety criteria | open |
