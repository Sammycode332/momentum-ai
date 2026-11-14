import { fireEvent, render, screen } from '@testing-library/react'
import { fixtureJwt } from '../test/token'

const token = fixtureJwt()
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../auth/auth-client', () => ({ authClient: { getSession: async () => ({ data: { session: { token } } }) } }))
import { RecordsPage } from './RecordsPage'

describe('RecordsPage', () => {
  const fetchRecords = vi.fn()
  beforeEach(() => { fetchRecords.mockReset(); vi.stubGlobal('fetch', fetchRecords); vi.spyOn(window, 'confirm').mockReturnValue(true) })
  afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks() })
  it('shows an empty state only after a successful empty response', async () => {
    fetchRecords.mockResolvedValueOnce(Response.json([]))
    render(<RecordsPage domain="projects" />)
    expect(screen.getByRole('status', { name: 'Loading records' })).toBeInTheDocument()
    expect(await screen.findByText('No projects yet')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
  it('shows a populated list and sends authenticated delete requests', async () => {
    const project = { id: 'p1', name: 'Website', description: null, status: 'in_progress', created_at: '', updated_at: '' }
    fetchRecords.mockResolvedValueOnce(Response.json([project])).mockResolvedValueOnce(new Response(null, { status: 204 }))
    render(<RecordsPage domain="projects" />)
    expect(await screen.findByText('Website')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))
    expect(await screen.findByText('No projects yet')).toBeInTheDocument()
    expect(fetchRecords.mock.calls[1][0]).toBe('/api/v1/projects/p1')
    expect(fetchRecords.mock.calls[1][1].headers.get('Authorization')).toBe(`Bearer ${token}`)
  })
})
