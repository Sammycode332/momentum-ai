import { Commitments } from './Commitments'
import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { loadOnboarding } from '../onboarding/onboarding-api'
import { listRecords } from '../records/records-api'
import { ApiRequestError } from '../auth/authenticated-fetch'
import type { Domain, RecordItem } from '../records/records-api'
import { summarizeDashboard } from './dashboard-data'
import type { DashboardRecords } from './dashboard-data'
import './dashboard.css'

type Destination = Domain | 'assistant' | 'goals' | 'notifications'
type Props = {
  name?: string
  onNavigate: (page: Destination) => void
  onCreate: (domain: 'tasks' | 'projects') => void
}
type Load = { state: 'loading' } | { state: 'error'; message: string }
  | { state: 'ready'; records: DashboardRecords }

const domains = ['projects', 'tasks', 'learning', 'academics', 'opportunities'] as const
const dayFormat = new Intl.DateTimeFormat(undefined, { weekday: 'long', month: 'long', day: 'numeric' })
const shortDate = new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', timeZone: 'UTC' })
const formatDate = (date: string) => shortDate.format(new Date(date + 'T00:00:00Z'))
const label = (value: string | null) => value?.replaceAll('_', ' ') ?? ''

export function Dashboard({ name, onNavigate, onCreate }: Props) {
  const [load, setLoad] = useState<Load>({ state: 'loading' })
  const [attempt, setAttempt] = useState(0)
  const [focus, setFocus] = useState<string>()
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const nextDay = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1)
    const timeout = window.setTimeout(() => setNow(new Date()), Math.max(0, nextDay.getTime() - Date.now()))
    return () => window.clearTimeout(timeout)
  }, [now])

  useEffect(() => {
    const controller = new AbortController()
    const { signal } = controller
    void Promise.all(domains.map(async domain => {
      const records = await listRecords(domain, signal)
      if (!Array.isArray(records)) throw new Error('Invalid records response.')
      return [domain, records] as const
    })).then(entries => {
      if (!signal.aborted) setLoad({ state: 'ready', records: Object.fromEntries(entries) as DashboardRecords })
    }, error => {
      if (!signal.aborted) setLoad({
        state: 'error',
        message: error instanceof ApiRequestError
          ? error.message + (error.code?.startsWith('NEON_') ? ` (${error.code})` : '')
          : 'Check your connection and try again.',
      })
    })
    return () => controller.abort()
  }, [attempt])

  useEffect(() => {
    const controller = new AbortController()
    void loadOnboarding(controller.signal).then(preferences => {
      if (!controller.signal.aborted && preferences?.status === 'completed') setFocus(preferences.primary_focus)
    }, () => { /* Preferences are optional for the dashboard. */ })
    return () => controller.abort()
  }, [])

  return (
    <section className="dashboard" aria-labelledby="dashboard-title">
      <header className="dashboard-welcome">
        <div>
          <p className="eyebrow">{dayFormat.format(now)}</p>
          <h1 id="dashboard-title">{name ? `Welcome, ${name}` : 'Welcome to Momentum'}</h1>
          <p>See what’s due and how your work is progressing.</p>
          {focus && <p className="dashboard-focus"><strong>Primary focus</strong> {focus}</p>}
        </div>
        <div className="dashboard-actions">
          <button className="button-secondary" onClick={() => onCreate('projects')}>New project</button>
          <button className="button-primary" onClick={() => onCreate('tasks')}>+ New task</button>
        </div>
      </header>
      {load.state === 'loading' && <DashboardSkeleton />}
      {load.state === 'error' && (
        <div className="error-state">
          <h2>Overview could not load</h2>
          <p role="alert">{load.message}</p>
          <button className="button-secondary" onClick={() => {
            setLoad({ state: 'loading' })
            setAttempt(value => value + 1)
          }}>Retry overview</button>
        </div>
      )}
      {load.state === 'ready' && <Snapshots records={load.records} now={now} onNavigate={onNavigate} />}
      <Commitments onNavigate={onNavigate} /><aside className="dashboard-assistant">
        <span className="dashboard-symbol" aria-hidden="true">✦</span>
        <div><h2>AI Assistant</h2><p>Build a plan around your goals and the time you have.</p></div>
        <button className="button-secondary" onClick={() => onNavigate('assistant')}>Open assistant</button>
      </aside>
    </section>
  )
}

function DashboardSkeleton() {
  return (
    <div className="dashboard-loading" role="status" aria-label="Loading overview">
      <div className="dashboard-metrics" aria-hidden="true">
        {[0, 1, 2, 3].map(key => <div className="dashboard-metric skeleton" key={key}><span /><span /></div>)}
      </div>
      <div className="dashboard-columns" aria-hidden="true">
        {[0, 1].map(key => <div className="dashboard-panel skeleton" key={key}><span /><span /></div>)}
      </div>
    </div>
  )
}

function Panel({ title, count, empty, action, children }: {
  title: string; count: number; empty: string; action: { label: string; run: () => void }; children: ReactNode
}) {
  return (
    <section className="dashboard-panel">
      <header><h2>{title}</h2><button className="text-button" onClick={action.run}>{action.label}</button></header>
      {count ? <ul>{children}</ul> : <p className="dashboard-empty">{empty}</p>}
    </section>
  )
}

function SnapshotRow({ title, detail, status }: { title: string | null; detail?: ReactNode; status?: string }) {
  return (
    <li className="dashboard-row">
      <div><strong>{title}</strong>{detail && <p>{detail}</p>}</div>
      {status && <span className="badge">{status}</span>}
    </li>
  )
}

function Opportunity({ item }: { item: RecordItem }) {
  return <SnapshotRow title={item.name} status={label(item.application_stage ?? item.status)}
    detail={[item.type, item.application_deadline && formatDate(item.application_deadline)].filter(Boolean).join(' · ')} />
}

function Snapshots({ records, now, onNavigate }: {
  records: DashboardRecords; now: Date; onNavigate: Props['onNavigate']
}) {
  const summary = summarizeDashboard(records, now)
  const metrics = [
    { title: 'Active projects', value: summary.projects.length, icon: '◫', detail: 'Open work' },
    { title: 'Outstanding tasks', value: summary.outstanding, icon: '≡', detail: 'Incomplete' },
    { title: 'Completed tasks', value: summary.completed, icon: '✓', detail: 'All time' },
    { title: 'Upcoming deadlines', value: summary.deadlines.length, icon: '◷', detail: 'Next 7 days' },
  ] as const

  return (
    <>
      <dl className="dashboard-metrics">
        {metrics.map(metric => <div className="dashboard-metric" key={metric.title}>
          <dt><span className="dashboard-symbol" aria-hidden="true">{metric.icon}</span>{metric.title}</dt>
          <dd><strong>{metric.value}</strong><small>{metric.detail}</small></dd>
        </div>)}
      </dl>
      <div className="dashboard-columns">
        <div className="dashboard-stack">
          <Panel title="Today’s priorities" count={summary.priorities.length} empty="You have no tasks due today or overdue."
            action={{ label: 'View tasks', run: () => onNavigate('tasks') }}>
            {summary.priorities.slice(0, 5).map(task => (
              <SnapshotRow key={task.id} title={task.title} status={task.priority ? `${task.priority} priority` : undefined}
                detail={task.due_date === summary.today ? 'Due today' : `Overdue · ${formatDate(task.due_date!)}`} />
            ))}
          </Panel>
          <Panel title="Project progress" count={summary.projects.length} empty="Your active projects will appear here."
            action={{ label: 'View projects', run: () => onNavigate('projects') }}>
            {summary.projects.slice(0, 4).map(({ project, done, total }) => (
              <li className="dashboard-project" key={project.id}>
                <div><strong>{project.name}</strong><span>{total ? `${done} of ${total} tasks` : 'No linked tasks'}</span></div>
                {total > 0 && <progress max={total} value={done} aria-label={`${project.name} task completion`} />}
              </li>
            ))}
          </Panel>
          <Panel title="Learning snapshot" count={summary.learning.length} empty="Add a learning objective to track it here."
            action={{ label: 'View learning', run: () => onNavigate('learning') }}>
            {summary.learning.slice(0, 4).map(item => (
              <SnapshotRow key={item.id} title={item.subject} detail={item.objective} status={label(item.progress_status)} />
            ))}
          </Panel>
        </div>
        <div className="dashboard-stack">
          <Panel title="Upcoming deadlines" count={summary.deadlines.length} empty="No open deadlines in the next seven days."
            action={{ label: 'View academics', run: () => onNavigate('academics') }}>
            {summary.deadlines.slice(0, 5).map(item => (
              <SnapshotRow key={`${item.category}-${item.id}`} title={item.title} detail={item.category} status={formatDate(item.date)} />
            ))}
          </Panel>
          <Panel title="Opportunity snapshot" count={summary.opportunities.length} empty="Your active opportunities will appear here."
            action={{ label: 'View opportunities', run: () => onNavigate('opportunities') }}>
            {summary.opportunities.slice(0, 4).map(item => <Opportunity key={item.id} item={item} />)}
          </Panel>
        </div>
      </div>
    </>
  )
}
