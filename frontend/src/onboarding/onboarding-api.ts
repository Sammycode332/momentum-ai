import { authenticatedFetch, requireSuccess } from '../auth/authenticated-fetch'

export type Preferences = {
  primary_focus: string
  current_goals: string
  planning_time: string
}

export type Onboarding =
  | ({ status: 'completed' } & Preferences)
  | { status: 'skipped'; primary_focus: null; current_goals: null; planning_time: null }

async function request<T>(suffix = '', options: RequestInit = {}): Promise<T> {
  const response = await authenticatedFetch(`/api/v1/onboarding${suffix}`, options)
  await requireSuccess(response, 'Planning preferences are temporarily unavailable. Please try again.')
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
