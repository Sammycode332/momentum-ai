# Testing Strategy

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
