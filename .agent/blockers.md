# Blockers and Open Questions

Resolved entries remain in this file with their history; none have been resolved yet.

| ID | Type | Blocker / question | Impact | Possible resolution | Status |
| --- | --- | --- | --- | --- | --- |
| BLK-01 | Decision | Repository layout and bootstrap approach for the selected React + TypeScript + Vite frontend are unselected | Blocks initial project structure, scripts, test tooling, and UI work | Decide repository layout and bootstrap approach without assuming a monorepo or separate repositories | open |
| BLK-02 | Requirement | Onboarding fields and initial dashboard composition are unspecified | Risks building irrelevant context collection or dashboard | Confirm smallest required fields and dashboard priorities | open |
| BLK-03 | Security/product | Boundaries and defaults for routine reprioritization/rescheduling are undefined | Unsafe or surprising agent actions; blocks AI-03 | Define consent, routine versus consequential changes, limits, approval gates, audit, reversal, and failure handling | open |
| BLK-04 | Infrastructure | AI provider, hosting, environments, scheduling, monitoring, migrations, and cost limits are undecided | Blocks selecting a minimal online MVP deployment baseline and production operations | Select services deliberately; distinguish MVP deployment from later hardening; update ADR-006 | open |
| BLK-05 | Data/security | Data retention/deletion expectations and AI-provider data handling terms are unknown | Cannot finalize privacy controls or logging policy | Confirm policy and provider agreement before handling production data | open |
| BLK-06 | Quality | Success metrics and test data for AI recommendations are unselected | Evaluation pass/fail thresholds cannot be finalized | Define scenario fixtures, expected outcomes, and critical safety criteria | open |
