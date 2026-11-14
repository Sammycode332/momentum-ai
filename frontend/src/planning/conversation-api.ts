import { authenticatedFetch, requireSuccess } from '../auth/authenticated-fetch'
import type { ChatTurn } from './planning-api'

export type Conversation = { id: string; title: string; updated_at: string }
export type TaskEdit = {
  field: 'title' | 'status' | 'priority' | 'due_date'
  previous: string | null
  value: string
}
export type GoalDetails = { title: string; description: string | null; target_date: string | null }
export type Roadmap = {
  goal: GoalDetails
  weekly_hours: number
  stages: { milestone: string; project: string; deliverable: string; prerequisite: string | null; deadline: string;
    tasks: { title: string; due_date: string; hours: number }[] }[]
}
export type PlanReceipt = {
  goal_id: string; project_ids: string[]; milestone_ids: string[]; task_ids: string[]; selected: number[]
}
export type ChatAction = {
  id: string
  status: 'pending' | 'applied' | 'rejected'
  result_id: string | null
  proposal: { kind: 'create_task' | 'update_task' | 'create_goal' | 'save_roadmap'; title: string;
    priority: string; due_date: string | null; edit?: TaskEdit | null;
    goal?: GoalDetails | null; roadmap?: Roadmap | null; receipt?: PlanReceipt | null }
}
export type SavedMessage = ChatTurn & { turn_id: string; position: number; action?: ChatAction | null }

async function request<T>(path = '', method = 'GET', body?: object, signal?: AbortSignal): Promise<T> {
  const response = await authenticatedFetch(`/api/v1/ai/conversations${path}`, {
    method, signal,
    ...(body && { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  })
  await requireSuccess(response, 'Could not access conversations. Try again.')
  return response.status === 204 ? undefined as T : response.json()
}

export const listConversations = (signal: AbortSignal) => request<Conversation[]>('', 'GET', undefined, signal)
export const loadMessages = (id: string, signal: AbortSignal) => request<SavedMessage[]>(`/${id}/messages`, 'GET', undefined, signal)
export const createConversation = (title: string, signal: AbortSignal) => request<Conversation>('', 'POST', { title }, signal)
export const renameConversation = (id: string, title: string) => request<Conversation>(`/${id}`, 'PATCH', { title })
export const deleteConversation = (id: string) => request<void>(`/${id}`, 'DELETE')
export const sendTurn = (id: string, turn: SavedMessage, signal: AbortSignal) =>
  request<SavedMessage>(`/${id}/turns`, 'POST', {
    turn_id: turn.turn_id, content: turn.content,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
  }, signal)
