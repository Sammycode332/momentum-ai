import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'

import { createGoal, deleteGoal, listGoals, updateGoal } from './goals-api'
import type { Goal } from './goals-api'
import './goals.css'

export function Goals() {
  const [goals, setGoals] = useState<Goal[] | null>(null)
  const [loadFailed, setLoadFailed] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [loadAttempt, setLoadAttempt] = useState(0)
  const [title, setTitle] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveFeedback, setSaveFeedback] = useState<'success' | 'error' | null>(null)
  const [editing, setEditing] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [actionError, setActionError] = useState('')
  const [notice, setNotice] = useState('')
  const [filter, setFilter] = useState('all')
  const [query, setQuery] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    listGoals(controller.signal).then(
      (savedGoals) => {
        if (!controller.signal.aborted) setGoals(savedGoals)
      },
      (error) => {
        if (!controller.signal.aborted) {
          setLoadError(error instanceof Error ? error.message : 'Goals are temporarily unavailable.')
          setLoadFailed(true)
        }
      },
    )
    return () => controller.abort()
  }, [loadAttempt])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const cleanedTitle = title.trim()
    if (!cleanedTitle || goals === null || saving) return

    setSaving(true)
    setSaveFeedback(null)
    try {
      const goal = await createGoal(cleanedTitle)
      setGoals((current) => [goal, ...(current ?? [])])
      setTitle('')
      setSaveFeedback('success')
    } catch {
      setSaveFeedback('error')
    } finally {
      setSaving(false)
    }
  }

  async function changeGoal(goal: Goal, changes: { title?: string; completed?: boolean }) {
    if (saving) return
    setSaving(true)
    setActionError('')
    setNotice('')
    try {
      const saved = await updateGoal(goal.id, changes)
      setGoals(current => current?.map(item => item.id === saved.id ? saved : item) ?? null)
      if (changes.title !== undefined) setEditing(null)
      setNotice(changes.completed === true ? 'Goal completed.' : changes.completed === false ? 'Goal reopened.' : 'Goal updated.')
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Could not update your goal. Try again.')
    } finally { setSaving(false) }
  }

  async function remove(goal: Goal) {
    if (saving || !window.confirm(`Delete “${goal.title}”? This cannot be undone.`)) return
    setSaving(true)
    setActionError('')
    setNotice('')
    try {
      await deleteGoal(goal.id)
      setGoals(current => current?.filter(item => item.id !== goal.id) ?? null)
      if (editing === goal.id) setEditing(null)
      setNotice('Goal deleted.')
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Could not delete your goal. Try again.')
    } finally { setSaving(false) }
  }

  const visibleGoals = goals?.filter(goal => goal.title.toLocaleLowerCase().includes(query.toLocaleLowerCase())
    && (filter === 'all' || (filter === 'completed' ? goal.completed : !goal.completed))) ?? []

  return (
    <section aria-labelledby="goals-title" className="settings-panel">
      <h2 id="goals-title">Personal Goals</h2>
      <p className="state-copy">Define what matters. Turn a clear intention into steady progress.</p>
      {loadFailed ? (
        <div className="state-block">
          <p role="alert" className="feedback-error">Could not load your goals. {loadError}</p>
          <button
            type="button"
            className="text-button"
            onClick={() => {
              setLoadFailed(false)
              setLoadError('')
              setLoadAttempt((attempt) => attempt + 1)
            }}
          >
            Retry loading goals
          </button>
        </div>
      ) : goals === null ? (
        <p role="status" className="state-copy">Loading goals…</p>
      ) : (
        <>
          <form className="goal-form" onSubmit={submit}>
            <label htmlFor="goal-title">Goal title</label>
            <div className="inline-form">
              <input
                id="goal-title"
                className="field"
                value={title}
                onChange={(event) => {
                  setTitle(event.target.value)
                  setSaveFeedback(null)
                }}
                disabled={saving}
                maxLength={200}
                required
              />
              <button
                type="submit"
                disabled={saving || !title.trim()}
                className="button-primary"
              >
                {saving ? 'Saving…' : 'Add goal'}
              </button>
            </div>
          </form>
          {saveFeedback === 'success' && <p role="status" className="feedback-success">Goal saved.</p>}
          {saveFeedback === 'error' && <p role="alert" className="feedback-error">Could not save your goal. Try again.</p>}
          {actionError && <p role="alert" className="feedback-error">{actionError}</p>}
          {notice && <p role="status" className="feedback-success">{notice}</p>}
          {goals.length === 0 ? (
            <p className="state-copy">No goals yet.</p>
          ) : (
            <>
              <div className="goal-toolbar">
                <label>Search goals<input className="field" type="search" value={query} onChange={e => setQuery(e.target.value)} /></label>
                <label>Show goals<select className="field" value={filter} onChange={e => setFilter(e.target.value)}>
                  <option value="all">All goals</option><option value="active">Active</option><option value="completed">Completed</option>
                </select></label>
                <p className="state-copy">{goals.filter(goal => goal.completed).length} of {goals.length} completed</p>
              </div>
              {!visibleGoals.length && <p className="state-copy">No goals match your filters.</p>}
              <ul className="goal-list">
                {visibleGoals.map(goal => <li key={goal.id} className="goal-row">
                  {editing === goal.id ? <form className="goal-edit" aria-label="Edit goal" onSubmit={event => {
                    event.preventDefault()
                    if (editTitle.trim()) void changeGoal(goal, { title: editTitle.trim() })
                  }}>
                    <label>Goal name<input className="field" autoFocus required maxLength={200} value={editTitle}
                      disabled={saving} onChange={e => setEditTitle(e.target.value)} /></label>
                    <div className="goal-actions">
                      <button className="button-primary" disabled={saving || !editTitle.trim()}>Save goal</button>
                      <button className="button-secondary" type="button" disabled={saving} onClick={() => setEditing(null)}>Cancel edit</button>
                    </div>
                  </form> : <>
                    <div className="goal-label"><strong>{goal.title}</strong><span className="badge">{goal.completed ? 'Completed' : 'Active'}</span></div>
                    <div className="goal-actions">
                      <button className="button-secondary" disabled={saving} aria-label={`${goal.completed ? 'Reopen' : 'Complete'} ${goal.title}`}
                        onClick={() => void changeGoal(goal, { completed: !goal.completed })}>{goal.completed ? 'Reopen' : 'Mark complete'}</button>
                      <button className="text-button" disabled={saving} aria-label={`Edit ${goal.title}`} onClick={() => {
                        setEditing(goal.id); setEditTitle(goal.title); setActionError(''); setNotice('')
                      }}>Edit</button>
                      <button className="text-button" disabled={saving} aria-label={`Delete ${goal.title}`} onClick={() => void remove(goal)}>Delete</button>
                    </div>
                  </>}
                </li>)}
              </ul>
            </>
          )}
        </>
      )}
    </section>
  )
}
