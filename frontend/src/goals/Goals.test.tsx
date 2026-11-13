import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { Goals } from './Goals'

vi.mock('../auth/auth-client', () => ({
  authClient: {
    getSession: vi.fn().mockResolvedValue({ data: { session: { token: 'test-token' } } }),
  },
}))

const goal = { id: 'test-id', title: 'Read ten pages', created_at: '2026-11-12T10:00:00Z' }

describe('Personal Goals', () => {
  const fetchGoals = vi.fn()

  beforeEach(() => {
    fetchGoals.mockReset()
    vi.stubGlobal('fetch', fetchGoals)
  })

  afterEach(() => vi.unstubAllGlobals())

  it('loads, creates, and reloads a saved goal with the existing session', async () => {
    fetchGoals
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(Response.json(goal, { status: 201 }))
      .mockResolvedValueOnce(Response.json([goal]))

    const first = render(<Goals />)
    expect(screen.getByText('Loading goals…')).toBeInTheDocument()
    expect(await screen.findByText('No goals yet.')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Goal title'), { target: { value: goal.title } })
    fireEvent.click(screen.getByRole('button', { name: 'Add goal' }))

    expect(await screen.findByText('Goal saved.')).toBeInTheDocument()
    expect(screen.getByRole('listitem')).toHaveTextContent(goal.title)
    const [path, request] = fetchGoals.mock.calls[1]
    expect(path).toBe('/api/v1/goals')
    expect(request.method).toBe('POST')
    expect(request.headers.get('Authorization')).toBe('Bearer test-token')
    expect(JSON.parse(request.body)).toEqual({ title: goal.title })

    first.unmount()
    render(<Goals />)
    expect(await screen.findByRole('listitem')).toHaveTextContent(goal.title)
  })

  it('lets users retry a failed load and keeps the title after a failed save', async () => {
    fetchGoals
      .mockResolvedValueOnce(new Response(null, { status: 503 }))
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(new Response(null, { status: 503 }))
    render(<Goals />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load your goals.')
    fireEvent.click(screen.getByRole('button', { name: 'Retry loading goals' }))
    expect(await screen.findByText('No goals yet.')).toBeInTheDocument()
    const input = screen.getByLabelText('Goal title')
    fireEvent.change(input, { target: { value: goal.title } })
    fireEvent.click(screen.getByRole('button', { name: 'Add goal' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Could not save your goal.')
    expect(input).toHaveValue(goal.title)
  })
})
