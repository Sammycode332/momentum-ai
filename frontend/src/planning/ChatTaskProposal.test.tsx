import { fireEvent, render, screen } from '@testing-library/react'
import { expect, it, vi } from 'vitest'
import { api } from '../features/api'
import { RecordsPage } from '../records/RecordsPage'
import { listRecords } from '../records/records-api'
import { ConversationAssistant } from './ConversationAssistant'
import type { ChatAction, SavedMessage } from './conversation-api'

vi.mock('../features/api', () => ({ api: vi.fn() }))
vi.mock('../records/records-api', () => ({ listRecords: vi.fn() }))

const pending: ChatAction = {
  id: 'proposal-1', status: 'pending', result_id: null,
  proposal: { kind: 'create_task', title: 'learn system design', priority: 'high', due_date: '2026-11-15' },
}
const message: SavedMessage = {
  turn_id: 'turn-1', position: 1, role: 'assistant', content: 'Review the proposal.', action: pending,
}

it('shows a pending proposal, reports failure, then displays confirmed creation and loads the task on mount', async () => {
  const applied = { ...pending, status: 'applied', result_id: 'task-1' }
  vi.mocked(api).mockRejectedValueOnce(new Error('Storage unavailable.')).mockResolvedValueOnce(applied)
  const chat = render(<ConversationAssistant chatId="chat-1" initialMessages={[message]} />)
  expect(screen.getByText(/Pending approval/)).toBeInTheDocument()
  expect(screen.queryByText(/Task created/)).not.toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Approve and create task' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Storage unavailable.')
  expect(screen.queryByText(/Task created/)).not.toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Approve and create task' }))
  expect(await screen.findByText('Task created. Find it in Tasks.')).toBeInTheDocument()
  expect(api).toHaveBeenLastCalledWith('actions/proposal-1/approve', 'POST')
  chat.unmount()

  vi.mocked(listRecords).mockResolvedValueOnce([{
    id: 'task-1', title: 'learn system design', priority: 'high', due_date: '2026-11-15',
    status: 'not_started', created_at: '', updated_at: '',
  }])
  render(<RecordsPage domain="tasks" />)
  expect(await screen.findByRole('heading', { name: 'learn system design' })).toBeInTheDocument()
})

it('shows rejection without a success state', async () => {
  vi.mocked(api).mockResolvedValueOnce({ ...pending, status: 'rejected' })
  render(<ConversationAssistant chatId="chat-1" initialMessages={[message]} />)
  fireEvent.click(screen.getByRole('button', { name: 'Reject proposal' }))
  expect(await screen.findByText('Proposal rejected.')).toBeInTheDocument()
  expect(screen.queryByText(/Task created/)).not.toBeInTheDocument()
  expect(api).toHaveBeenLastCalledWith('actions/proposal-1/reject', 'POST')
})

it('shows the current and proposed value and confirms an approved update', async () => {
  const action: ChatAction = {
    ...pending,
    proposal: { ...pending.proposal, kind: 'update_task', edit: { field: 'status', previous: 'not_started', value: 'completed' } },
  }
  vi.mocked(api).mockResolvedValueOnce({ ...action, status: 'applied', result_id: 'task-1' })
  render(<ConversationAssistant chatId="chat-1" initialMessages={[{ ...message, action }]} />)
  expect(screen.getByText('not started')).toBeInTheDocument()
  expect(screen.getByText('completed')).toBeInTheDocument()
  expect(screen.queryByText(/Task updated/)).not.toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Approve task update' }))
  expect(await screen.findByText('Task updated. Find it in Tasks.')).toBeInTheDocument()
})

it('reviews the roadmap and approves only selected phases using the server receipt', async () => {
  const goal = { title: 'Learn backend AI', description: 'Build a portfolio', target_date: '2027-05-14' }
  const stage = { milestone: 'Ship an API', project: 'API project', deadline: '2027-01-14', deliverable: 'Working demo',
    prerequisite: null, tasks: [{ title: 'Draft API contract', due_date: '2026-12-14', hours: 2 }] }
  const action: ChatAction = { ...pending, proposal: { ...pending.proposal, kind: 'save_roadmap', title: goal.title,
    roadmap: { goal, weekly_hours: 4, stages: [stage, { ...stage, milestone: 'Ship an evaluation suite' }] } } }
  const receipt = { goal_id: 'goal-1', project_ids: ['project-1'], milestone_ids: ['milestone-1'], task_ids: ['task-1'], selected: [0] }
  vi.mocked(api).mockResolvedValueOnce({ ...action, status: 'applied', result_id: 'goal-1', proposal: { ...action.proposal, receipt } })
  render(<ConversationAssistant chatId="chat-1" initialMessages={[{ ...message, action }]} />)
  expect(screen.getAllByText(/Draft API contract/)).toHaveLength(2)
  expect(screen.queryByText(/Goal saved/)).not.toBeInTheDocument()
  fireEvent.click(screen.getByRole('checkbox', { name: 'Save phase 2' }))
  fireEvent.click(screen.getByRole('button', { name: 'Save goal and selected phases' }))
  expect(await screen.findByText(/Saved 1 project, 1 milestone and 1 task/)).toBeInTheDocument()
  expect(api).toHaveBeenLastCalledWith('actions/proposal-1/approve', 'POST', { stages: [0] })
})
