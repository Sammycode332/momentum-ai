import { fireEvent, render, screen } from '@testing-library/react'
import { expect, it, vi } from 'vitest'
import { Dashboard } from './Dashboard'
import { loadOnboarding } from '../onboarding/onboarding-api'
import { listRecords } from '../records/records-api'

vi.mock('../auth/auth-client', () => ({ authClient: {} }))
vi.mock('../onboarding/onboarding-api')
vi.mock('../goals/goals-api', () => ({ listGoals: vi.fn().mockResolvedValue([]) }))
vi.mock('../features/api', async importOriginal => ({
  ...await importOriginal<typeof import('../features/api')>(),
  api: vi.fn().mockResolvedValue([]),
}))
vi.mock('../records/records-api', { spy: true })

it('retries a failed load, keeps optional personalization, and offers both creation actions', async () => {
  vi.mocked(loadOnboarding).mockResolvedValue({
    status: 'completed', primary_focus: 'Research', current_goals: 'Private details', planning_time: '08:00',
  })
  const lists = vi.mocked(listRecords).mockResolvedValue([])
  lists.mockRejectedValueOnce(new Error('Offline'))
  const create = vi.fn()
  const navigate = vi.fn()
  render(<Dashboard name="Maya" onCreate={create} onNavigate={navigate} />)

  expect(screen.getByRole('status', { name: 'Loading overview' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Welcome, Maya' })).toBeInTheDocument()
  expect(await screen.findByText('Research')).toBeInTheDocument()
  expect(screen.queryByText('Private details')).not.toBeInTheDocument()
  expect(await screen.findByRole('alert')).toBeInTheDocument()
  expect(screen.queryByText('Active projects')).not.toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: 'Retry overview' }))
  expect(await screen.findByText('No open deadlines in the next seven days.')).toBeInTheDocument()
  expect(lists.mock.calls.slice(5).map(([domain]) => domain)).toEqual([
    'projects', 'tasks', 'learning', 'academics', 'opportunities',
  ])
  fireEvent.click(screen.getByRole('button', { name: '+ New task' }))
  fireEvent.click(screen.getByRole('button', { name: 'New project' }))
  fireEvent.click(screen.getByRole('button', { name: 'Open assistant' }))
  expect(create.mock.calls).toEqual([['tasks'], ['projects']])
  expect(navigate).toHaveBeenCalledWith('assistant')
})
