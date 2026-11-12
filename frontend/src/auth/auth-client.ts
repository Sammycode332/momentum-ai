import { createAuthClient } from '@neondatabase/auth'
import { BetterAuthReactAdapter } from '@neondatabase/auth/react/adapters'

const authUrl = import.meta.env.VITE_NEON_AUTH_URL

if (!authUrl) {
  throw new Error('VITE_NEON_AUTH_URL is required to use Neon Auth.')
}

export const authClient = createAuthClient(authUrl, {
  adapter: BetterAuthReactAdapter(),
})
