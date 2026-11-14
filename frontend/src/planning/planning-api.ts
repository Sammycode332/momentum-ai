import { authenticatedFetch, requireSuccess } from '../auth/authenticated-fetch'

type Reference = { id: string; title: string }

export type Plan = {
  title: string
  summary: string
  total_minutes: number
  activities: {
    title: string
    duration_minutes: number
    reason: string
    task: Reference | null
    project: Reference | null
  }[]
  deadline_considerations: string[]
}

async function requestAssistant(
  route: 'plan' | 'chat',
  request: object,
  signal: AbortSignal,
) {
  const response = await authenticatedFetch(`/api/v1/ai/${route}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal,
  })
  await requireSuccess(response, response.status === 429
    ? 'The assistant has reached a temporary request limit. Wait a moment and retry.'
    : response.status === 404 || response.status === 405
      ? 'The assistant endpoint is missing. Check that the current backend is running.'
      : `The assistant service could not respond (HTTP ${response.status}). Retry or check the backend connection.`)
  return response.json().catch(() => null)
}

export async function generatePlan(
  request: { objective: string; available_minutes: number; focus_area?: string },
  signal: AbortSignal,
): Promise<Plan> {
  const body = await requestAssistant('plan', request, signal)
  if (!Array.isArray(body?.activities) || !Array.isArray(body?.deadline_considerations)) {
    throw new Error('The planning service returned an unreadable plan. Try again.')
  }
  return body as Plan
}

export type ChatTurn = { role: 'user' | 'assistant'; content: string }

export async function sendChat(messages: ChatTurn[], signal: AbortSignal): Promise<string> {
  const body = await requestAssistant('chat', { messages }, signal)
  if (typeof body?.reply !== 'string' || !body.reply.trim() || body.reply.length > 4000) {
    throw new Error('The assistant returned an unreadable reply. Try again.')
  }
  return body.reply
}
