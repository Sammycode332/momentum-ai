import type { Domain, RecordItem } from '../records/records-api'

export type DashboardRecords = Record<Domain, RecordItem[]>

export function dateKey(date: Date) {
  const pad = (value: number) => String(value).padStart(2, '0')
  return [date.getFullYear(), pad(date.getMonth() + 1), pad(date.getDate())].join('-')
}

const active = (status: string | null) => status === 'not_started' || status === 'in_progress'
const priority = new Map([['high', 0], ['medium', 1], ['low', 2]])
const byDate = (a: string, b: string) => a.localeCompare(b)

function datedRecords(records: RecordItem[], field: string, title: string, category: string) {
  return records.flatMap(record => {
    const date = record[field]
    return date && record.status !== 'completed'
      ? [{ id: record.id, title: record[title], date, category }]
      : []
  })
}

export function summarizeDashboard(records: DashboardRecords, now: Date) {
  const today = dateKey(now)
  const end = dateKey(new Date(now.getFullYear(), now.getMonth(), now.getDate() + 6))
  const outstanding = records.tasks.filter(task => task.status !== 'completed')
  const priorities = outstanding
    .filter(task => task.due_date && task.due_date <= today)
    .sort((a, b) => byDate(a.due_date!, b.due_date!)
      || (priority.get(a.priority ?? '') ?? 3) - (priority.get(b.priority ?? '') ?? 3)
      || a.id.localeCompare(b.id))
  const deadlines = [
    ...datedRecords(records.tasks, 'due_date', 'title', 'Task'),
    ...datedRecords(records.academics, 'deadline', 'activity', 'Academic'),
    ...datedRecords(records.opportunities, 'application_deadline', 'name', 'Opportunity'),
  ].filter(item => item.date >= today && item.date <= end)
    .sort((a, b) => byDate(a.date, b.date) || a.title?.localeCompare(b.title ?? '') || a.id.localeCompare(b.id))

  const taskCounts = new Map<string, { done: number; total: number }>()
  for (const task of records.tasks) {
    if (!task.project_id) continue
    const count = taskCounts.get(task.project_id) ?? { done: 0, total: 0 }
    count.total += 1
    if (task.status === 'completed') count.done += 1
    taskCounts.set(task.project_id, count)
  }
  const projects = records.projects.filter(project => active(project.status)).map(project => ({
    project,
    ...taskCounts.get(project.id) ?? { done: 0, total: 0 },
  }))
  const opportunities = records.opportunities.filter(item => active(item.status)).sort((a, b) => {
    const order = (item: RecordItem) => item.application_deadline && item.application_deadline >= today ? 0 : 1
    return order(a) - order(b) || byDate(a.application_deadline ?? '9999', b.application_deadline ?? '9999')
  })
  return {
    today, priorities, deadlines, projects, opportunities,
    outstanding: outstanding.length,
    completed: records.tasks.length - outstanding.length,
    learning: records.learning.filter(item => item.progress_status !== 'completed'),
  }
}
