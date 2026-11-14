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
- The built document and bundled proxy set `strict-origin` to keep recovery query values out of subrequest referrers. Verify hosted ingress log redaction using a synthetic recovery callback before launch.

## Evidence this increment

13 account/auth backend tests passed using synthetic fixtures; 2 recovery component
tests passed with a mocked provider. Frontend build and lint passed. No real data
export, reset email, OAuth authorization, deployment or migration was performed.

## Unresolved release risks

- The Phase 9 read-only development catalog audit confirmed active RLS on all 20
  expected tables with the restricted app role. Synthetic cross-user tests cover
  selected workflows. Full table-by-table SQL and HTTP coverage remains open.
- The owner verified fresh sign-in, Overview cold reload and sign-out. The initial
  intermittent rejection's exact root cause was never captured.
  Phase 9 added one same-account refresh for eligible reads and claim rejection before
  signing-key lookup. Successful authentication still requires signature verification.
- Full account deletion, revocation coordination, audit retention and backup erasure
  procedures remain undefined/unimplemented.
- Export uses offset pagination, not a frozen snapshot; concurrent writes can affect
  completeness. Large exports need an operator workflow beyond the browser limit.
- Frontend Auth findings were triaged below. Backend package vulnerability scanning,
  image/action pinning and container runtime verification remain open.
- The owner verified direct Windows push. Scheduled delivery is at-least-once and
  remains blocked at restricted worker authentication. Check subscription cleanup at sign-out.
- Global AI spend caps, production monitoring, TLS/ingress trust, provider retention
  agreements and backup/rollback rehearsals are still operator release gates.

## Neon Auth dependency advisories — 2026-11-14

The deployed frontend image serves Vite output through Nginx. FastAPI verifies
Neon-issued JWTs and does not run a Better Auth server. A Vite emitted-module
inventory found the Better Auth client (including a Magic Link client descriptor)
and Zod. It found no emitted OAuth Proxy or Magic Link server handler, Drizzle
adapter, auth UI package, email renderer, html-to-text or deepmerge. Locally
installed package versions do not establish the managed Neon service's patch or
plugin status. Momentum's Google button configuration only controls the frontend.

| Finding | Locked chain and patch | Application reachability and status |
| --- | --- | --- |
| [GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5), High, CVSS 7.5 | `@neondatabase/auth@0.6.0-beta` and transitive Auth packages → `zod@4.5.4`; patched since `4.6.6`. | The parser shipped in browser assets. No Momentum-owned server request parsing path uses Zod. No app path was identified that validates attacker-controlled oversized collections in the browser. Targeted override updates all locked Zod copies to `4.6.7`. |
| [GHSA-965c-763c-88jm](https://github.com/advisories/GHSA-965c-763c-88jm), Critical, CVSS 9.1 | `@neondatabase/auth@0.6.0-beta` → `better-auth@1.7.6`, directly and through `@neondatabase/auth-ui@0.4.0-beta`. Patched in `1.7.7`. | Account impersonation requires the affected server-side combination of Magic Link, social or generic OAuth, and database-backed OAuth state. The local client does not host the vulnerable handler. Managed service exposure is unverified and gates release. |
| [GHSA-r4xp-prcw-77qf](https://github.com/advisories/GHSA-r4xp-prcw-77qf), High, CVSS 7.4 | Same `better-auth@1.7.6` chain; patched in `1.7.7`. | Account impersonation requires the affected server OAuth Proxy configuration and its advisory prerequisites, including cookie-backed state. No such server handler is shipped by Momentum. Confirm Neon-managed patch status or that the affected configuration is absent. |
| [GHSA-44jh-23m7-hpcf](https://github.com/advisories/GHSA-44jh-23m7-hpcf), Low, CVSS 3.7 | Same `better-auth@1.7.6` chain → `@better-auth/drizzle-adapter@1.7.6`; both patched in `1.7.7`. | Applies to affected Better Auth rate limiting backed by the Drizzle PostgreSQL adapter. Momentum's API rate controls use its own stack. No affected adapter runs locally in production. Managed configuration is unverified. |
| [GHSA-gcqx-w48m-w2h4](https://github.com/advisories/GHSA-gcqx-w48m-w2h4), Low, CVSS 5.3 | `@neondatabase/auth@0.6.0-beta` → `@neondatabase/auth-ui@0.4.0-beta` → `@daveyplate/better-auth-ui@3.4.0` → `@react-email/components@1.0.12` → `@react-email/render@2.0.6` → `html-to-text@9.0.5` → `deepmerge@4.3.1`; no patched deepmerge release. | Affected prototype-poisoning path needs attacker-controlled objects passed into the merge. The renderer chain is absent from deployed assets and FastAPI. `html-to-text@10.0.1` removes deepmerge via newer React Email render, but the installed parent pins `2.0.6`; defer changing this unused chain until upstream supports it. |

Full and `--omit=dev` npm audits agreed before and after the change. There were
no dev-only npm findings. After the Zod update, npm reports nine affected package
entries (one critical, eight low). These represent four distinct remaining
advisories (one critical, one high and two low); npm displays the maximum per
package. Latest observed Neon client `0.7.0-beta` still pins Zod `4.5.4`, Better Auth
`1.7.6` and the same auth UI version. A blanket Better Auth override would alter its
tightly coupled client/core/plugin stack and would not patch the managed server.
Require Neon confirmation of a patched service or non-applicability for the two
account-takeover advisories before public release. Revisit the pinned JS packages
when Neon publishes a supported fix. This check used package and bundle evidence.
