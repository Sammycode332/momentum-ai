import { fireEvent, render, screen } from '@testing-library/react'
import { fixtureJwt } from '../test/token'

const token = fixtureJwt()
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { Goals } from './Goals'

vi.mock('../auth/auth-client', () => ({
  authClient: {
    getSession: vi.fn().mockImplementation(async () => ({ data: { session: { token: token } } })),
  },
}))

const goal = { id: 'test-id', title: 'Read ten pages', created_at: '2026-11-12T10:00:00Z', completed: false }

describe('Personal Goals', () => {
  const fetchGoals = vi.fn()

  beforeEach(() => {
    fetchGoals.mockReset()
    vi.stubGlobal('fetch', fetchGoals)
  })

  afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks() })

  it('edits, completes, reopens and deletes a saved goal', async () => {
    const renamed = { ...goal, title: 'Read twenty pages' }
    fetchGoals.mockResolvedValueOnce(Response.json([goal]))
      .mockResolvedValueOnce(Response.json(renamed))
      .mockResolvedValueOnce(Response.json({ ...renamed, completed: true }))
      .mockResolvedValueOnce(Response.json(renamed))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    render(<Goals />)
    fireEvent.click(await screen.findByRole('button', { name: `Edit ${goal.title}` }))
    fireEvent.change(screen.getByLabelText('Goal name'), { target: { value: renamed.title } })
    fireEvent.click(screen.getByRole('button', { name: 'Save goal' }))
    expect(await screen.findByText('Goal updated.')).toBeInTheDocument()
    expect(JSON.parse(fetchGoals.mock.calls[1][1].body)).toEqual({ title: renamed.title })
    fireEvent.click(screen.getByRole('button', { name: `Complete ${renamed.title}` }))
    expect(await screen.findByText('Goal completed.')).toBeInTheDocument()
    expect(screen.getByText('1 of 1 completed')).toBeInTheDocument()
    expect(JSON.parse(fetchGoals.mock.calls[2][1].body)).toEqual({ completed: true })
    fireEvent.click(screen.getByRole('button', { name: `Reopen ${renamed.title}` }))
    expect(await screen.findByText('Goal reopened.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: `Delete ${renamed.title}` }))
    expect(await screen.findByText('No goals yet.')).toBeInTheDocument()
    expect(fetchGoals.mock.calls[4][1].method).toBe('DELETE')
    expect(fetchGoals.mock.calls[4][0]).toBe('/api/v1/goals/test-id')
  })

  it('preserves edits after failure and cancels deletion without an API request', async () => {
    fetchGoals.mockResolvedValueOnce(Response.json([goal]))
      .mockResolvedValueOnce(new Response(null, { status: 503 }))
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    render(<Goals />)
    fireEvent.click(await screen.findByRole('button', { name: `Edit ${goal.title}` }))
    fireEvent.change(screen.getByLabelText('Goal name'), { target: { value: 'Keep this draft' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save goal' }))
    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.getByLabelText('Goal name')).toHaveValue('Keep this draft')
    fireEvent.click(screen.getByRole('button', { name: 'Cancel edit' }))
    fireEvent.click(screen.getByRole('button', { name: `Delete ${goal.title}` }))
    expect(fetchGoals).toHaveBeenCalledTimes(2)
    expect(screen.getByText(goal.title)).toBeInTheDocument()
  })

  it('filters saved goals without changing records or fabricating progress', async () => {
    fetchGoals.mockResolvedValueOnce(Response.json([goal, { ...goal, id: 'second', title: 'Finish portfolio', completed: true }]))
    render(<Goals />)
    expect(await screen.findByText('1 of 2 completed')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Show goals'), { target: { value: 'active' } })
    expect(screen.queryByText('Finish portfolio')).not.toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Search goals'), { target: { value: 'missing' } })
    expect(screen.getByText('No goals match your filters.')).toBeInTheDocument()
    expect(fetchGoals).toHaveBeenCalledTimes(1)
  })

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
    expect(request.headers.get('Authorization')).toBe(`Bearer ${token}`)
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
