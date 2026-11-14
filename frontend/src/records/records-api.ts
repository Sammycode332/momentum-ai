import { authenticatedFetch, requireSuccess } from '../auth/authenticated-fetch'

export type Domain = 'projects' | 'tasks' | 'learning' | 'academics' | 'opportunities'
export type RecordItem = Record<string, string | null> & { id: string; created_at: string; updated_at: string }
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await authenticatedFetch(`/api/v1/${path}`, options)
  await requireSuccess(response, 'We could not complete that request. Please try again.')
  return response.status === 204 ? undefined as T : response.json() as Promise<T>
}
export function listRecords(domain: Domain, signal: AbortSignal) { return request<RecordItem[]>(domain, { signal }) }
export function createRecord(domain: Domain, value: object) { return request<RecordItem>(domain, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(value) }) }
export function updateRecord(domain: Domain, id: string, value: object) { return request<RecordItem>(`${domain}/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(value) }) }
export function deleteRecord(domain: Domain, id: string) { return request<void>(`${domain}/${id}`, { method: 'DELETE' }) }
