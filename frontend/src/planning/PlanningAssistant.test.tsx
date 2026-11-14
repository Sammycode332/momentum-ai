import { act, fireEvent, render, screen } from '@testing-library/react'
import { fixtureJwt } from '../test/token'

const token = fixtureJwt()
import { afterEach, expect, it, vi } from 'vitest'
import { PlanningAssistant } from './PlanningAssistant'

vi.mock('../auth/auth-client', () => ({
  authClient: { getSession: async () => ({ data: { session: { token } } }) },
}))

afterEach(() => vi.unstubAllGlobals())

it('generates an authenticated plan and displays ordered suggestions', async () => {
  let complete!: (response: Response) => void
  const fetchPlan = vi.fn(() => new Promise<Response>(resolve => { complete = resolve }))
  vi.stubGlobal('fetch', fetchPlan)
  render(<PlanningAssistant />)
  fireEvent.change(screen.getByLabelText('Planning objective'), { target: { value: ' Outline my essay ' } })
  fireEvent.change(screen.getByLabelText('Available time'), { target: { value: '45' } })
  await act(async () => fireEvent.click(screen.getByRole('button', { name: 'Generate plan' })))
  expect(screen.getByRole('status')).toHaveTextContent('drafting a plan')
  expect(screen.getByRole('button', { name: 'Generating…' })).toBeDisabled()
  expect(fetchPlan).toHaveBeenCalledWith('/api/v1/ai/plan', expect.objectContaining({
    method: 'POST', headers: expect.any(Headers),
    body: JSON.stringify({ objective: 'Outline my essay', available_minutes: 45 }),
  }))
  complete(Response.json({
    title: 'Essay session', summary: 'Start with an outline.', total_minutes: 20,
    activities: [{
      title: 'Draft an outline', duration_minutes: 20, reason: 'The draft is due first.',
      task: { id: 'task-id', title: 'Essay draft' }, project: null,
    }],
    deadline_considerations: ['Leave time for review.'],
  }))
  expect(await screen.findByRole('heading', { name: 'Essay session' })).toBeInTheDocument()
  expect(screen.getByText('Task · Essay draft')).toBeInTheDocument()
  expect(screen.getByRole('status')).toHaveTextContent('20 of 45 min')
  expect(screen.getByText(/Your saved records haven’t changed/)).toBeInTheDocument()
})

it('shows safe API errors and preserves the inputs for retry', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json(
    { error: { message: 'Planning timed out. Please try again.' } }, { status: 504 },
  )))
  render(<PlanningAssistant />)
  const objective = screen.getByLabelText('Planning objective')
  fireEvent.change(objective, { target: { value: 'Revise the draft' } })
  fireEvent.click(screen.getByRole('button', { name: 'Generate plan' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Planning timed out.')
  expect(objective).toHaveValue('Revise the draft')
  expect(screen.getByRole('button', { name: 'Generate plan' })).toBeEnabled()
})
