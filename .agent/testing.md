# Testing Strategy

## Goal lifecycle acceptance

CORE-03 adds signed-principal API tests for partial title/completion updates, complete/reopen, deletion, nonexistent/foreign IDs, spoofed owners, invalid/null fields, unauthenticated mutation and inactive-RLS failure. UI tests exercise edit → complete → reopen → delete, cancelled deletion, retained failed edits and filtering/counts from saved records. The SQL goals test now requires migrations 001 and 005 plus the restricted grants; it no longer accepts missing UPDATE permission as sufficient isolation proof. It must demonstrate owner update/delete success and cross-user denial in a rolled-back transaction.

## Release reliability regressions — 2026-11-13

- Sign-out returned and thrown failures show safe retry feedback; a subsequent success refetches the session.
- Initial session acquisition failures are redacted; later requests recover. Concurrent-token tests wait for the observable acquisition event rather than assuming a fixed microtask count.
- Synthetic signed JWTs with future `iat` or `nbf` remain rejected; logs omit tokens and subjects.
- Core record POST/PUT reject overlong descriptions, NUL text and ownership injection before opening storage, across the five domains.
- Run `python -m app.schema_audit` for read-only table/RLS/grant metadata. It does not inspect private records, apply migrations or substitute for isolation tests.
- Browser evidence: observed rejected Overview, then a successful signed-in Overview after restoring the local development server. Hard-refresh lifecycle and Network correlation are unfinished because Computer Use stopped on URL-confidence enforcement.

Testing must demonstrate behavior and safety, with controlled fixtures or test copies for any test that modifies user records. Never target uncontrolled user data.

## Tooling and commands

- **Frontend:** Vitest runs React unit/component tests in jsdom with React Testing Library and @testing-library/jest-dom. From frontend/, run npm run test.
- **Backend:** pytest runs unit/integration tests. FastAPI route behavior uses the synchronous fastapi.testclient.TestClient, backed by httpx. From backend/, install the test extra with python -m pip install -e ".[test]", then run python -m pytest.

FND-03 does not add browser automation, external databases, mocking frameworks, or async-test plugins. Tests use application-local commands; no root test runner is selected.

## Controlled fixture policy

- Use synthetic, non-secret identities only. The baseline fixtures provide distinct user_a, user_b, and privileged_actor principals; they are test data, not Neon Auth users, real JWTs, or privileged database credentials.
- Each test creates only the records it needs and cleans up its own mutable state. Tests must never target a developer, staging, or production account, database, or provider.
- Authorization/isolation tests use at least two distinct fixture users. They must prove cross-user access is denied rather than relying on frontend filtering.
- Privileged-access tests must separately prove verified caller identity, explicit authorization, and owner filtering. A privileged fixture may not be treated as evidence that access is permitted.
- Add database-backed fixtures only after the database and migration approach are approved; they must use an isolated test database or transaction/cleanup strategy.

## Test layers

- **Unit:** validation, prioritization logic, permission checks, memory state transitions, provider adapters, and output parsing.
- **Integration:** FastAPI routes/services with authenticated identities; database constraints/RLS; Neon Auth and Neon PostgreSQL integration; approved AI-provider mock/contract behavior.
- **ID-02 database foundation:** unit tests use a fake connection and synthetic settings to cover configuration precedence, enforced transport options, the read-only query, connection cleanup, and redacted failures. The opt-in Neon development check is `python -m app.database` from `backend/`; setup is documented in [configuration](configuration.md).
- **API:** authentication failures, malformed input, resource ownership, error behavior, and only authorized response fields.
- **Frontend:** onboarding, private-route handling, core record workflows, dashboard states, accessibility-relevant interactions, and safe rendering of AI output.
- **ID-01 authentication:** cover session loading, unauthenticated and authenticated rendering, session revalidation after OTP verification, sign-in, and sign-out, and safe provider errors for invalid credentials, duplicate registration, and `EMAIL_NOT_VERIFIED`. Exercise the direct verification-code entry, resend requests, and expired-code and resend errors. Backend tests use synthetic signed tokens to check the returned subject and credential rejection. For live regression checks, use the configured Neon branch to verify registration, email OTP, sign-in, refresh, logout, and protected API access. Record the outcome without copying passwords, codes, tokens, or cookies.
- **Authorization/isolation:** two or more fixture users must prove cross-user list/read/create/update/delete attempts are denied at API and database-policy boundaries. Tests must separately cover user-scoped/RLS paths and privileged database paths; privileged-path tests must prove verified identity, explicit authorization, and ownership filters prevent cross-user access despite any RLS bypass.
- **Database escape hatches:** test views, RPCs, privileged functions, and administrative access paths before use. Security review must confirm that each preserves the intended authorization boundary and does not silently bypass tenant isolation.
- **Regression:** add a test when fixing a relevant defect; run the affected suite before completion.

## AI behavior evaluations

Use deterministic fixtures/stubs where feasible and separate critical safety/correctness gates from presentation or convenience scoring. Critical requirements must pass; good wording cannot compensate for unsafe access, unauthorized writes, fabricated context, or bypassed approval.

Initial scenarios:

1. **Cross-domain prioritization:** given conflicting project, learning, academic, and commitment data, recommend a realistic, evidenced next action and avoid unjustified certainty.
2. **Memory and project continuity:** use approved prior context appropriately, preserve project continuity, and never treat unapproved proposals as memory.
3. **Learning support:** propose a learning action matched to recorded skill goals and available constraints without inventing progress.
4. **Career opportunity matching:** relate a saved opportunity to the user’s authenticated profile/goals while keeping data private and explaining the match basis.
5. **Safe autonomy and task recovery:** allow only consented routine reprioritization and rescheduling, require approval for consequential changes, log every action, and preserve a clear recovery/reversal path; reject out-of-scope changes.

Record scenario fixtures, expected critical outcomes, test commands, and pass/fail evidence once tooling is chosen.


## 2026-11-13 focused checks

- Backend existing suite: 87 passed, 2 isolated PostgreSQL tests skipped.
- tests/test_release_features.py: 12 passed; disabled personalization, tutor progression constraints, quiet-hour/DST behavior, untrusted push destinations, source deduplication, applied-action retry, memory input boundaries, authenticated routes and oversized request rejection. Uses synthetic fixtures, no live AI generations. New usage store is stubbed in existing API tests to prevent live writes; its concurrent database enforcement still needs isolated PostgreSQL validation.
- Frontend suite: 43 passed before final navigation consolidation. Final consolidation checked with npm run build and npm run lint (both passed). No broad suite repetition for reversible navigation/style changes.
- Browser: localhost preview timed out; no screenshots or final visual/accessibility review.

## 2026-11-14 incremental verification

`python -m pytest tests/test_account.py tests/test_app.py -q`: 13 passed. Covers export owner scoping, bounded pagination, secret-section denial, missing authentication, offset bounds and liveness alongside auth regressions. Synthetic fixtures only.
`npm test -- src/auth/PasswordRecovery.test.tsx --reporter=dot`: 2 passed. Covers fixed-origin callback/generic messaging and URL-token removal/matching-password submission using a mocked SDK.
Final `npm run build` and `npm run lint` passed. No broad suite repetition. Container verification could not run because Docker engine was unavailable. Read-only schema audit could not connect; no remote state was verified or changed.

## Feature-first checkpoint 2026-11-14

Owner asked to build missing features before broader testing. For connected productivity/chat workflows, ran frontend build/lint and backend import/enum-validation checks only; no new broad suite or real mutations. New database migration/application, responsive browser behavior and end-to-end proposal/reminder/project flows remain unverified. Read-only storage diagnostic failed at runtime authentication and printed only safe categories.

Notification usability checkpoint: API import plus valid/oversized batch validation checked without database/provider access; broad workflow suites deferred. Browser and live worker verification remain pending.

## Chat task creation regression

- `test_chat_actions.py` covers invalid provider output, timezone boundaries, unconfirmed claims, and the opt-in restricted PostgreSQL lifecycle using signed synthetic identities and a rolled-back outer transaction. It uses the normal chat, approve/reject, and Tasks list APIs. It also forces a write-path failure after insertion to check rollback, retries approval to check deduplication, and verifies an outsider cannot act on the proposal.
- `ChatTaskProposal.test.tsx` checks pending, failure, retry, confirmed success, rejection, and rendering the saved task on Tasks mount. The frontend test uses API fixtures. A separate live Gemini smoke request verified extraction of the synthetic reproduction. The owner subsequently verified the request, approval, and saved task in a real signed-in browser.
- Backend suite with restricted development PostgreSQL fixtures: 123 passed. Focused chat task suite including direct RLS assertions: 15 passed. Frontend suite: 47 passed. Production build and lint passed.

## Workspace reads and task edits

- Focused backend suite: 66 passed, including owner-isolated workspace answers and the approval, rollback, rejection, retry, and fresh Tasks-fetch checks through the restricted development PostgreSQL role. Synthetic records were rolled back.
- Final local workspace and task checks: 25 passed, including the saved-chat timezone route and stale proposal rejection. Focused frontend suite: 6 passed. Production build passed. The owner subsequently verified workspace reads and approved task edits in a real signed-in browser.

## Goal creation and roadmap approval

- Focused restricted PostgreSQL and backend suite: 51 passed. Used signed synthetic subjects and rolled-back records. Verified goal listing, selective roadmap approval, real goal/project/milestone/subtask links, replay receipts, rejection, late transaction failure, and cross-user API denial.
- Goal draft and workspace progress checks: 10 passed. Verified timezone-aware calendar-month boundaries, ambiguous drafts, malformed provider output and provider failure. A separate synthetic Gemini roadmap generation matched the schema and date bounds.
- Frontend goal and review tests: 9 passed. Build and lint passed. Signed-in browser acceptance remains outstanding for Milestone C.
