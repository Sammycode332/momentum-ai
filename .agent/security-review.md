# Security review checkpoint — 2026-11-14

This is a scoped engineering checkpoint, not a penetration test or certification.

## Reviewed controls

- Backend JWT verification derives identity; private exports use active RLS plus
  explicit owner predicates. Unknown export sections cannot select arbitrary tables.
- Export pages are limited to 200 rows. Push keys/endpoints, credentials and tokens
  are excluded by field/table allowlists. Browser download is bounded and cancelled
  exports do not produce a partial file. Multi-page consistency is explicitly limited.
- Recovery delegates to Neon SDK methods. The callback uses the current origin;
  request messages do not confirm account existence. Token query parameters are
  removed from the visible URL and not placed in browser storage or logs.
- Google OAuth is hidden by default pending operator configuration. No credentials
  are placed in public build variables.
- Existing controls include user-approved memory, typed action proposals,
  idempotent applied-action retry, bounded AI requests, body limits and generic push.
- `.env` files remain ignored; container contexts also exclude environment files.

## Evidence this increment

13 account/auth backend tests passed using synthetic fixtures; 2 recovery component
tests passed with a mocked provider. Frontend build and lint passed. No real data
export, reset email, OAuth authorization, deployment or migration was performed.

## Unresolved release risks

- New-table SQL/RLS and cross-user HTTP isolation have not been demonstrated against
  a migrated disposable database. Read-only development catalog audit could not connect.
- Cold-load token rejection lacks a confirmed root cause and final browser evidence.
- Full account deletion, revocation coordination, audit retention and backup erasure
  procedures remain undefined/unimplemented.
- Export uses offset pagination, not a frozen snapshot; concurrent writes can affect
  completeness. Large exports need an operator workflow beyond the browser limit.
- Backend dependencies/images and CI actions are not fully pinned to reviewed hashes;
  a dependency vulnerability scan and container runtime check remain required.
- Push delivery is at-least-once, subscription/device behavior is unverified, and
  provider credentials/hosting are not activated. Test sign-out subscription cleanup.
- Global AI spend caps, production monitoring, TLS/ingress trust, provider retention
  agreements and backup/rollback rehearsals are still operator release gates.
