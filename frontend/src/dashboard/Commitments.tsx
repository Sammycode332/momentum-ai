import { useEffect, useState } from 'react'
import { listGoals } from '../goals/goals-api'
import type { Goal } from '../goals/goals-api'
import { api, errorText } from '../features/api'
type Reminder = { id: string; title: string; due_at: string; status: string }
export function Commitments({ onNavigate }: { onNavigate: (page: 'goals' | 'notifications') => void }) {
  const [goals, setGoals] = useState<Goal[]>(), [reminders, setReminders] = useState<Reminder[]>(), [errors, setErrors] = useState<Record<string, string>>({}), [retry, setRetry] = useState(0)
  useEffect(() => {
    const c = new AbortController()
    listGoals(c.signal).then(rows => { if (!c.signal.aborted) { setGoals(rows); setErrors(old => ({ ...old, goals: '' })) } }).catch(e => { if (!c.signal.aborted) setErrors(old => ({ ...old, goals: errorText(e) })) })
    api<Reminder[]>('reminders', 'GET', undefined, c.signal).then(rows => { if (!c.signal.aborted) { setReminders(rows); setErrors(old => ({ ...old, reminders: '' })) } }).catch(e => { if (!c.signal.aborted) setErrors(old => ({ ...old, reminders: errorText(e) })) })
    return () => c.abort()
  }, [retry])
  const active = goals?.filter(goal => !goal.completed)
  const upcoming = reminders?.filter(reminder => reminder.status === 'scheduled').sort((a, b) => a.due_at.localeCompare(b.due_at)).slice(0, 5)
  return <div className="dashboard-columns commitment-panels"><section className="dashboard-panel"><header><h2>Your goals</h2><button className="text-button" onClick={() => onNavigate('goals')}>View goals</button></header>{errors.goals ? <p role="alert">{errors.goals} <button className="text-button" onClick={() => setRetry(n => n + 1)}>Retry</button></p> : !goals ? <p role="status">Loading goals…</p> : <><p className="state-copy">{active?.length} active · {goals.filter(goal => goal.completed).length} completed</p>{active?.length ? <ul>{active.slice(0, 4).map(goal => <li className="dashboard-row" key={goal.id}><strong>{goal.title}</strong></li>)}</ul> : <p className="dashboard-empty">Choose a goal to give your next steps direction.</p>}</>}</section><section className="dashboard-panel"><header><h2>Scheduled reminders</h2><button className="text-button" onClick={() => onNavigate('notifications')}>View reminders</button></header>{errors.reminders ? <p role="alert">{errors.reminders} <button className="text-button" onClick={() => setRetry(n => n + 1)}>Retry</button></p> : !reminders ? <p role="status">Loading reminders…</p> : upcoming?.length ? <ul>{upcoming.map(item => <li className="dashboard-row" key={item.id}><div><strong>{item.title}</strong><p>{new Date(item.due_at).toLocaleString()}</p></div></li>)}</ul> : <p className="dashboard-empty">Add a reminder from a record or Notifications.</p>}</section></div>
}
