import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'

import { createGoal, listGoals } from './goals-api'
import type { Goal } from './goals-api'

export function Goals() {
  const [goals, setGoals] = useState<Goal[] | null>(null)
  const [loadFailed, setLoadFailed] = useState(false)
  const [loadAttempt, setLoadAttempt] = useState(0)
  const [title, setTitle] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveFeedback, setSaveFeedback] = useState<'success' | 'error' | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    listGoals(controller.signal).then(
      (savedGoals) => {
        if (!controller.signal.aborted) setGoals(savedGoals)
      },
      () => {
        if (!controller.signal.aborted) setLoadFailed(true)
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

  return (
    <section aria-labelledby="goals-title" className="mt-8 border-t border-slate-700 pt-6">
      <h2 id="goals-title" className="text-xl font-semibold">Personal Goals</h2>
      {loadFailed ? (
        <div className="mt-3">
          <p role="alert" className="text-rose-300">Could not load your goals.</p>
          <button
            type="button"
            className="mt-2 text-sm text-cyan-300 underline"
            onClick={() => {
              setLoadFailed(false)
              setLoadAttempt((attempt) => attempt + 1)
            }}
          >
            Retry loading goals
          </button>
        </div>
      ) : goals === null ? (
        <p role="status" className="mt-3 text-slate-300">Loading goals…</p>
      ) : (
        <>
          <form className="mt-4 space-y-2" onSubmit={submit}>
            <label htmlFor="goal-title" className="block text-sm text-slate-200">Goal title</label>
            <div className="flex flex-wrap gap-2">
              <input
                id="goal-title"
                className="min-w-0 flex-1 rounded-md border border-slate-600 bg-slate-950 px-3 py-2"
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
                className="rounded-md bg-cyan-300 px-4 py-2 font-semibold text-slate-950 disabled:opacity-60"
              >
                {saving ? 'Saving…' : 'Add goal'}
              </button>
            </div>
          </form>
          {saveFeedback === 'success' && <p role="status" className="mt-2 text-cyan-200">Goal saved.</p>}
          {saveFeedback === 'error' && <p role="alert" className="mt-2 text-rose-300">Could not save your goal. Try again.</p>}
          {goals.length === 0 ? (
            <p className="mt-4 text-slate-300">No goals yet.</p>
          ) : (
            <ul className="mt-4 space-y-2">
              {goals.map((goal) => (
                <li key={goal.id} className="break-words rounded-md bg-slate-800 px-3 py-2">
                  {goal.title}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  )
}
