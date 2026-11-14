import { authenticatedFetch, requireSuccess } from '../auth/authenticated-fetch'

export async function api<T>(path: string, method = 'GET', body?: unknown, signal?: AbortSignal): Promise<T> {
  const response = await authenticatedFetch(`/api/v1/${path}`, { method, signal,
    ...(body === undefined ? {} : { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }) })
  await requireSuccess(response, 'This request could not be completed. Please try again.')
  return response.status === 204 ? undefined as T : response.json()
}
export const errorText = (error: unknown) => error instanceof Error ? error.message : 'Please try again.'
