import { authClient } from '../auth/auth-client'

export type Goal = {
  id: string
  title: string
  created_at: string
}

async function requestGoals<T>(options: RequestInit): Promise<T> {
  const session = await authClient.getSession()
  const token = session.data?.session?.token
  if (!token) throw new Error('An authenticated session is required.')

  const headers = new Headers(options.headers)
  headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch('/api/v1/goals', { ...options, headers, cache: 'no-store' })
  if (!response.ok) throw new Error('The goals request failed.')
  return response.json() as Promise<T>
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
