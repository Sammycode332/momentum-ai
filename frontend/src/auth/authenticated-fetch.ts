import { authClient } from './auth-client'

export class ApiRequestError extends Error {
  constructor(message: string, publicStatus: number, code?: string) {
    super(message)
    this.status = publicStatus
    this.code = code
  }

  readonly status: number
  readonly code?: string
}

const signInAgain = 'Your session has expired. Sign in again to continue.'
const sessionUnavailable = 'Neon Auth could not verify your session. Try again.'
let pendingToken: Promise<string> | undefined

function decodeSegment(segment: string) {
  return JSON.parse(atob(segment.replaceAll('-', '+').replaceAll('_', '/')))
}

function isFreshJwt(token: string | undefined): token is string {
  if (!token) return false
  try {
    const parts = token.split('.')
    if (parts.length !== 3 || parts.some(part => !part)) return false
    const claims = decodeSegment(parts[1])
    return decodeSegment(parts[0]).alg === 'EdDSA'
      && Number.isFinite(claims.exp) && claims.exp > Date.now() / 1000 + 15
  } catch {
    return false
  }
}

async function resolveToken() {
  const current = await authClient.getSession().catch(() => {
    throw new ApiRequestError(sessionUnavailable, 503, 'NEON_SESSION_UNAVAILABLE')
  })
  const token = current?.data?.session?.token
  if (isFreshJwt(token)) return token

  // X-Force-Fetch bypasses the installed Neon adapter's in-memory session cache.
  const fresh = await authClient.getSession({
    query: { disableCookieCache: true },
    fetchOptions: { headers: { 'X-Force-Fetch': 'true' } },
  }).catch(() => {
    throw new ApiRequestError(sessionUnavailable, 503, 'NEON_SESSION_UNAVAILABLE')
  })
  const refreshedToken = fresh?.data?.session?.token
  if (isFreshJwt(refreshedToken)) return refreshedToken
  if (fresh?.error && fresh.error.status !== 401 && fresh.error.status !== 403) {
    throw new ApiRequestError(sessionUnavailable, 503, 'NEON_SESSION_UNAVAILABLE')
  }
  if (fresh?.data?.session) {
    throw new ApiRequestError(
      'Neon Auth returned a session without a usable access token. Try again.',
      503, 'NEON_TOKEN_UNAVAILABLE',
    )
  }
  throw new ApiRequestError(signInAgain, 401, 'NEON_SESSION_ENDED')
}

export async function authenticatedFetch(path: string, options: RequestInit = {}) {
  options.signal?.throwIfAborted()
  const token = await (pendingToken ??= resolveToken().finally(() => { pendingToken = undefined }))
  options.signal?.throwIfAborted()
  const headers = new Headers(options.headers)
  headers.set('Authorization', `Bearer ${token}`)
  return fetch(path, { ...options, headers, cache: 'no-store' })
}

export async function requireSuccess(response: Response, fallback: string) {
  if (response.ok) return
  const body = await response.json().catch(() => null)
  const code = typeof body?.error?.code === 'string' ? body.error.code : undefined
  let message = typeof body?.error?.message === 'string' ? body.error.message : fallback
  if (response.status === 401) {
    message = code === 'ACCESS_TOKEN_EXPIRED' || code === 'UNAUTHORIZED'
      ? signInAgain
      : 'The API rejected your access token. Try again or sign in again if the problem persists.'
  }
  const requestId = response.headers.get('X-Request-ID')
  const reference = (response.status === 401 || response.status >= 500) && requestId && /^[a-f0-9]{32}$/.test(requestId)
    ? ` Reference: ${requestId}.` : ''
  throw new ApiRequestError(
    message + reference, response.status, code,
  )
}
