import { authClient } from '../auth/auth-client'

export type Preferences = {
  primary_focus: string
  current_goals: string
  planning_time: string
}

export type Onboarding =
  | ({ status: 'completed' } & Preferences)
  | { status: 'skipped'; primary_focus: null; current_goals: null; planning_time: null }

async function request<T>(suffix = '', options: RequestInit = {}): Promise<T> {
  const session = await authClient.getSession()
  const token = session?.data?.session?.token
  if (!token) throw new Error('An authenticated session is required.')

  const headers = new Headers(options.headers)
  headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`/api/v1/onboarding${suffix}`, {
    ...options,
    headers,
    cache: 'no-store',
  })
  if (!response.ok) throw new Error('The onboarding request failed.')
  return response.json() as Promise<T>
}

export function loadOnboarding(signal: AbortSignal) {
  return request<Onboarding | null>('', { signal })
}

export function saveOnboarding(preferences: Preferences) {
  return request<Onboarding>('', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(preferences),
  })
}

export function skipOnboarding() {
  return request<Onboarding>('/skip', { method: 'POST' })
}
