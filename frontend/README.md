# Momentum AI frontend

React, TypeScript, Vite and Tailwind CSS v4. See the root README for complete setup.

Copy `.env.example` to `.env`, configure the public Neon Auth URL, then run `npm ci` and `npm run dev`.
The development proxy targets `http://127.0.0.1:8001`; override `MOMENTUM_DEV_API_TARGET` before starting Vite when needed.

Checks: `npm run lint`, `npm test`, `npm run build`.

`VITE_SUPPORT_EMAIL` configures the public contact link in Settings. `VITE_GOOGLE_SIGN_IN_ENABLED=true` displays Google sign-in only after the operator has configured and verified Google OAuth in Neon. Never put provider secrets or database credentials in Vite variables.

Password recovery uses Neon request/reset methods and a same-origin `/?flow=reset-password` return address. The reset token is kept in component memory and removed from the visible URL. Email delivery, trusted origins, and callback behavior need live verification in each deployment.

The assistant has Chat, Learn, Interview and Approvals modes. Settings groups profile, memory and data export. The service worker handles optional generic push notifications and does not cache private API responses.

The Dockerfile prepares a same-origin frontend/API topology; see `.agent/deployment.md` at the repository root. Container and browser/device validation remain release gates.
