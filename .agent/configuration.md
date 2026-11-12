# Environment, Configuration, and Secrets Conventions

This document establishes the FND-02 configuration boundary. It does not select a hosting provider, secret manager, AI provider, or runtime configuration library.

## Repository convention

Real environment files are ignored throughout the repository: `.env` and `.env.*`. Placeholder-only templates named `.env.example` or `.env.*.example` may be committed. Templates must contain no real credentials, project URLs, tokens, or environment-specific values.

Do not place secrets in source files, documentation examples, build artifacts, prompts, logs, error messages, or committed environment files. If a secret is accidentally committed, treat it as exposed: revoke or rotate it through the owning service and remove it through the approved incident/repository procedure.

## Environment use

### Local development

Developers may supply configuration through ignored environment files or process environment variables. The frontend's Vite tooling can load its supported `.env` files. The backend loads its ignored local `.env` file for the Neon Auth verification settings without overriding process-managed values.

Neon Auth session cookies are managed by Neon Auth. For local browser authentication, configure the exact frontend origin in Neon Auth's trusted origins (including scheme, host, and port, such as `http://localhost:5173`). `localhost` and `127.0.0.1` are different origins. If the configured origin is not trusted or the browser rejects the session cookie, a successful credential request cannot survive the SDK's session refresh; application code must not replace that cookie with a token stored in browser storage.

When Neon Auth requires email verification, it creates an unverified user and delays session creation. This Neon Auth branch sends verification codes (OTP), so the frontend submits the email and code through the official client rather than relying on a callback URL. The branch must keep email/password authentication, required verification, an email provider, and the exact trusted frontend origin configured. These provider settings are not stored in this repository.

### Staging and production

The eventual hosting environment injects runtime configuration and secrets. They are configured separately for each environment and are never copied into the repository. This convention deliberately does not select a host, deployment platform, secret manager, or environment naming scheme beyond local, staging, and production.

## Public browser configuration

In Vite, variables with the `VITE_` prefix are available to browser code through `import.meta.env`. Treat every `VITE_*` value as public: it can be present in the compiled client bundle and visible to users. Use this prefix only for non-sensitive client configuration, such as a future public API base URL.

Never use `VITE_*` for credentials, private tokens, AI API keys, database credentials, signing secrets, or other privileged material. Frontend visibility and route guards are not authorization controls.

The Neon Auth URL is public browser configuration. It may be present in a `VITE_*` variable, but a browser session or token is never authorization proof for backend or database access until verified server-side and protected with RLS where applicable.

## Backend-only configuration

Neon Auth JWKS and Auth base URLs, privileged database credentials, AI-provider API keys, database credentials, signing secrets, and server-only service endpoints are backend runtime configuration. Backend code must read only the configuration it needs, validate required values when that code is implemented, and avoid returning or logging values.

Choosing a backend settings library, dotenv loader, secret manager, provider SDK, exact variable names, or deployment integration is deferred until a feature needs it. Any later choice must preserve this public/private boundary and be recorded through the project decision process.

## Verification

When this convention changes, use `git check-ignore -v --no-index` to inspect the effective ignore rule for real environment paths and template exceptions. Confirm templates are trackable with `git ls-files --others --exclude-standard`. Inspect tracked filenames and the diff for accidental credential-bearing files or values, and run `git diff --check`.
