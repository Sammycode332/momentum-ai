import { expect, it } from 'vitest'
import type { RecordItem } from '../records/records-api'
import { summarizeDashboard } from './dashboard-data'

function record(id: string, fields: Record<string, string>): RecordItem {
  return { id, created_at: '', updated_at: '', status: 'in_progress', ...fields }
}

it('ranks due tasks, counts the local seven-day window, and calculates linked progress', () => {
  const summary = summarizeDashboard({
    projects: [record('p', { name: 'Release' }), record('archived', { status: 'paused' })],
    tasks: [
      record('low', { priority: 'low', due_date: '2026-12-30', project_id: 'p' }),
      record('high', { priority: 'high', due_date: '2026-12-30', project_id: 'p' }),
      record('late', { priority: 'low', due_date: '2026-12-29' }),
      record('done', { status: 'completed', due_date: '2026-12-30', project_id: 'p' }),
      record('undated', {}),
    ],
    academics: [record('end', { deadline: '2027-01-05', activity: 'Exam' }),
      record('outside', { deadline: '2027-01-06' })],
    opportunities: [record('offer', { application_deadline: '2027-01-02', name: 'Fellowship' })],
    learning: [record('learn', { progress_status: 'paused' }), record('finished', { progress_status: 'completed' })],
  }, new Date(2026, 11, 30, 23))

  expect(summary.priorities.map(task => task.id)).toEqual(['late', 'high', 'low'])
  expect(summary.deadlines.map(item => item.id)).toEqual(['high', 'low', 'offer', 'end'])
  expect(summary.projects).toMatchObject([{ project: { id: 'p' }, total: 3, done: 1 }])
  expect(summary).toMatchObject({ outstanding: 4, completed: 1, learning: [{ id: 'learn' }] })
})
