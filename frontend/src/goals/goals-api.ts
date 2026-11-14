import { authenticatedFetch, requireSuccess } from '../auth/authenticated-fetch'

export type Goal = {
  id: string
  title: string
  created_at: string
  completed: boolean
}

async function requestGoals<T>(options: RequestInit, suffix = ''): Promise<T> {
  const response = await authenticatedFetch(`/api/v1/goals${suffix}`, options)
  await requireSuccess(response, 'Goals are temporarily unavailable. Please try again.')
  return response.status === 204 ? undefined as T : response.json() as Promise<T>
}

export function listGoals(signal: AbortSignal) {
  return requestGoals<Goal[]>({ signal })
}

export function createGoal(title: string) {
  return requestGoals<Goal>({
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  })
}

export function updateGoal(id: string, changes: { title?: string; completed?: boolean }) {
  return requestGoals<Goal>({ method: 'PATCH', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(changes) }, `/${encodeURIComponent(id)}`)
}

export function deleteGoal(id: string) {
  return requestGoals<void>({ method: 'DELETE' }, `/${encodeURIComponent(id)}`)
}
