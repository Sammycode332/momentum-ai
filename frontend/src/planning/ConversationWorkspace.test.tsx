import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { ConversationWorkspace } from './ConversationWorkspace'
import { deleteConversation, listConversations, loadMessages } from './conversation-api'

vi.mock('./conversation-api', () => ({
  listConversations: vi.fn(), loadMessages: vi.fn(), deleteConversation: vi.fn(),
  createConversation: vi.fn(), renameConversation: vi.fn(), sendTurn: vi.fn(),
}))
vi.mock('./planning-api', () => ({ generatePlan: vi.fn() }))
vi.mock('../auth/authenticated-fetch', () => ({ ApiRequestError: Error }))

afterEach(() => {
  history.replaceState(null, '', '/')
  vi.restoreAllMocks()
})

it('restores saved messages from the URL after remount and deletes the active conversation', async () => {
  const id = '12345678-1234-1234-1234-123456789abc'
  history.replaceState(null, '', `/?chat=${id}`)
  vi.mocked(listConversations).mockResolvedValue([{ id, title: 'Study session', updated_at: '' }])
  vi.mocked(loadMessages).mockResolvedValue([
    { turn_id: 't', position: 1, role: 'user', content: 'What is normalization?' },
    { turn_id: 't', position: 1, role: 'assistant', content: '## Saved answer' },
  ])
  vi.mocked(deleteConversation).mockResolvedValue(undefined)
  vi.spyOn(window, 'confirm').mockReturnValue(true)
  const first = render(<ConversationWorkspace />)
  expect(await screen.findByRole('heading', { name: 'Saved answer' })).toBeInTheDocument()
  first.unmount()
  render(<ConversationWorkspace />)
  expect(await screen.findByText('What is normalization?')).toBeInTheDocument()
  expect(loadMessages).toHaveBeenCalledTimes(2)
  fireEvent.click(screen.getByRole('button', { name: 'Delete Study session' }))
  expect(await screen.findByText('No conversations yet.')).toBeInTheDocument()
  expect(screen.queryByText('Saved answer')).not.toBeInTheDocument()
  expect(deleteConversation).toHaveBeenCalledWith(id)
})
