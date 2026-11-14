import { fireEvent, render, screen } from '@testing-library/react'
import { expect, it, vi } from 'vitest'
import { ConversationAssistant } from './ConversationAssistant'
import { sendTurn } from './conversation-api'

vi.mock('./conversation-api', () => ({ sendTurn: vi.fn(), loadMessages: vi.fn().mockResolvedValue([]) }))
vi.mock('./planning-api', () => ({ generatePlan: vi.fn() }))

it('offers prompts, sends on Enter, and carries previous turns into a retryable follow-up', async () => {
  vi.mocked(sendTurn)
    .mockImplementationOnce(async (_, turn) => ({ ...turn, role: 'assistant', content: 'Start with one concept.' }))
    .mockRejectedValueOnce(new Error('Gemini is busy.'))
    .mockImplementationOnce(async (_, turn) => ({ ...turn, role: 'assistant', content: 'Here is an example.' }))
  render(<ConversationAssistant chatId="saved-chat" />)
  fireEvent.click(screen.getByRole('button', { name: /Learn/ }))
  const message = screen.getByRole('textbox', { name: 'Message' })
  expect(message).toHaveFocus()
  fireEvent.keyDown(message, { key: 'Enter', shiftKey: true })
  expect(sendTurn).not.toHaveBeenCalled()
  fireEvent.keyDown(message, { key: 'Enter' })
  expect(await screen.findByText('Start with one concept.')).toBeInTheDocument()
  fireEvent.change(message, { target: { value: 'Show me another example.' } })
  fireEvent.click(screen.getByRole('button', { name: 'Send' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Gemini is busy.')
  fireEvent.click(screen.getByRole('button', { name: 'Retry reply' }))
  expect(await screen.findByText('Here is an example.')).toBeInTheDocument()
  expect(vi.mocked(sendTurn).mock.calls[2][1]).toEqual(vi.mocked(sendTurn).mock.calls[1][1])
  expect(screen.getAllByText('Show me another example.')).toHaveLength(1)
  fireEvent.click(screen.getByRole('button', { name: 'Structured planner' }))
  expect(screen.getByLabelText('Planning objective')).toBeInTheDocument()
})
