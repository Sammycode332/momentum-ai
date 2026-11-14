import { afterEach, expect, it, vi } from 'vitest'
import { authenticatedFetch, requireSuccess } from './authenticated-fetch'
import { authClient } from './auth-client'
import { fixtureJwt } from '../test/token'

vi.mock('./auth-client', () => ({ authClient: { getSession: vi.fn() } }))
const getSession = vi.mocked(authClient.getSession)
const session = (token: string) => ({ data: { session: { token } } }) as Awaited<ReturnType<typeof getSession>>

afterEach(() => {
  getSession.mockReset()
  vi.unstubAllGlobals()
})

it.each(['opaque-session-token', fixtureJwt(1)])('waits for one fresh JWT for concurrent requests', async stale => {
  const fresh = fixtureJwt()
  let finish!: (value: ReturnType<typeof session>) => void
  getSession.mockResolvedValueOnce(session(stale))
    .mockImplementationOnce(() => new Promise(resolve => { finish = resolve }))
  const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
  vi.stubGlobal('fetch', fetchMock)
  const cancelled = new AbortController()
  const first = authenticatedFetch('/api/v1/tasks', { signal: cancelled.signal })
  const second = authenticatedFetch('/api/v1/projects')
  const firstResult = expect(first).rejects.toMatchObject({ name: 'AbortError' })
  await vi.waitFor(() => expect(getSession).toHaveBeenCalledTimes(2))
  expect(fetchMock).not.toHaveBeenCalled()
  expect(getSession).toHaveBeenCalledTimes(2)
  expect(getSession.mock.calls[1][0]).toMatchObject({ query: { disableCookieCache: true } })
  cancelled.abort()
  finish(session(fresh))
  await firstResult
  await second
  expect(fetchMock).toHaveBeenCalledTimes(1)
  expect(fetchMock.mock.calls[0][1].headers.get('Authorization')).toBe(`Bearer ${fresh}`)
})

it('distinguishes a restored session without a fresh token from an expired session', async () => {
  getSession.mockResolvedValue(session(fixtureJwt(1)))
  const fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  await expect(authenticatedFetch('/api/v1/tasks')).rejects.toMatchObject({
    status: 503, code: 'NEON_TOKEN_UNAVAILABLE',
  })
  expect(fetchMock).not.toHaveBeenCalled()
})

it('asks for sign-in when Neon confirms there is no session', async () => {
  getSession.mockResolvedValue({ data: null, error: null })
  await expect(authenticatedFetch('/api/v1/tasks')).rejects.toMatchObject({
    status: 401, code: 'NEON_SESSION_ENDED',
  })
})

it('redacts initial session failures and allows a later request to recover', async () => {
  getSession.mockRejectedValueOnce(new Error('private provider diagnostic'))
    .mockResolvedValueOnce(session(fixtureJwt()))
  const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
  vi.stubGlobal('fetch', fetchMock)
  await expect(authenticatedFetch('/api/v1/tasks')).rejects.toMatchObject({
    status: 503, code: 'NEON_SESSION_UNAVAILABLE',
    message: 'Neon Auth could not verify your session. Try again.',
  })
  expect(fetchMock).not.toHaveBeenCalled()
  await authenticatedFetch('/api/v1/tasks')
  expect(fetchMock).toHaveBeenCalledTimes(1)
})

it('surfaces an API 401 without refreshing or replaying the request', async () => {
  getSession.mockResolvedValue(session(fixtureJwt()))
  const fetchMock = vi.fn().mockResolvedValue(Response.json(
    { error: { code: 'INVALID_ACCESS_TOKEN' } }, { status: 401 },
  ))
  vi.stubGlobal('fetch', fetchMock)
  await expect(authenticatedFetch('/api/v1/ai/chat', { method: 'POST' })
    .then(response => requireSuccess(response, 'Unavailable'))).rejects.toThrow('The API rejected your access token')
  expect(getSession).toHaveBeenCalledTimes(1)
  expect(fetchMock).toHaveBeenCalledTimes(1)
})

it('shares one forced refresh across rejected reads and retries them once', async () => {
  const initial = fixtureJwt()
  const fresh = fixtureJwt(Math.floor(Date.now() / 1000) + 600)
  let finish!: (value: ReturnType<typeof session>) => void
  getSession.mockResolvedValueOnce(session(initial))
    .mockImplementationOnce(() => new Promise(resolve => { finish = resolve }))
  const fetchMock = vi.fn((path: string, options: RequestInit) => {
    if (path.endsWith('/tasks') && new Headers(options.headers).get('Authorization') === `Bearer ${fresh}`) {
      return Promise.resolve(Response.json([]))
    }
    return Promise.resolve(Response.json({ error: { code: 'INVALID_ACCESS_TOKEN' } }, { status: 401 }))
  })
  vi.stubGlobal('fetch', fetchMock)
  const requests = ['/api/v1/tasks', '/api/v1/projects'].map(path => authenticatedFetch(path))
  await vi.waitFor(() => expect(getSession).toHaveBeenCalledTimes(2))
  expect(fetchMock).toHaveBeenCalledTimes(2)
  finish(session(fresh))
  const responses = await Promise.all(requests)
  expect(responses.map(response => response.status)).toEqual([200, 401])
  expect(fetchMock).toHaveBeenCalledTimes(4)
  for (const [, options] of fetchMock.mock.calls.slice(2)) {
    expect(new Headers(options.headers).get('Authorization')).toBe(`Bearer ${fresh}`)
  }
})

it.each(['same token', 'different account', 'unrelated error'])('returns the original read rejection for %s', async scenario => {
  const initial = fixtureJwt()
  const fresh = scenario === 'different account' ? fixtureJwt(undefined, 'other-user') : initial
  getSession.mockResolvedValueOnce(session(initial)).mockResolvedValueOnce(session(fresh))
  const code = scenario === 'unrelated error' ? 'UNAUTHORIZED' : 'INVALID_ACCESS_TOKEN'
  const rejected = Response.json({ error: { code } }, { status: 401 })
  const fetchMock = vi.fn().mockResolvedValue(rejected)
  vi.stubGlobal('fetch', fetchMock)
  expect(await authenticatedFetch('/api/v1/tasks')).toBe(rejected)
  expect(getSession).toHaveBeenCalledTimes(scenario === 'unrelated error' ? 1 : 2)
  expect(fetchMock).toHaveBeenCalledTimes(1)
})

it('keeps a server diagnostic reference on a failed request', async () => {
  const requestId = '9a'.repeat(16)
  const response = Response.json({ error: { message: 'Unexpected failure.' } }, {
    status: 500, headers: { 'X-Request-ID': requestId },
  })
  await expect(requireSuccess(response, 'Unavailable')).rejects.toThrow(
    `Unexpected failure. Reference: ${requestId}.`,
  )
})
