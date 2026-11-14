import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { generatePlan } from './planning-api'
import type { Plan } from './planning-api'
import './planning.css'

type Result = { state: 'idle' | 'loading' } | { state: 'error'; message: string }
  | { state: 'ready'; plan: Plan; budget: number }

export function PlanningAssistant({ embedded = false }: { embedded?: boolean }) {
  const [objective, setObjective] = useState('')
  const [minutes, setMinutes] = useState(30)
  const [focus, setFocus] = useState('')
  const [result, setResult] = useState<Result>({ state: 'idle' })
  const pending = useRef<AbortController | null>(null)
  useEffect(() => () => pending.current?.abort(), [])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (pending.current || !objective.trim()) return
    const controller = new AbortController()
    pending.current = controller
    setResult({ state: 'loading' })
    try {
      const plan = await generatePlan({
        objective: objective.trim(), available_minutes: minutes, focus_area: focus.trim() || undefined,
      }, controller.signal)
      if (!controller.signal.aborted) setResult({ state: 'ready', plan, budget: minutes })
    } catch (error) {
      if (!controller.signal.aborted) setResult({
        state: 'error', message: error instanceof Error ? error.message : 'Try generating the plan again.',
      })
    } finally {
      pending.current = null
    }
  }

  return (
    <section className="planning" aria-label="Structured planner">
      {!embedded && <header className="planning-heading">
        <span className="planning-icon" aria-hidden="true">✦</span>
        <div><h1 id="planning-title">AI Assistant</h1><p>Turn a goal and a time budget into an ordered work plan.</p></div>
      </header>}
      <div className="planning-grid">
        <form className="planning-panel planning-form" onSubmit={submit}>
          <h2>Plan a session</h2>
          <fieldset disabled={result.state === 'loading'}>
            <label>Planning objective
              <textarea className="field" required maxLength={800} rows={4} value={objective}
                placeholder="What do you want to accomplish?" onChange={e => setObjective(e.target.value)} />
            </label>
            <label>Available time
              <select className="field" value={minutes} onChange={e => setMinutes(Number(e.target.value))}>
                {[5, 15, 30, 45, 60, 90, 120, 180, 240, 480].map(value => (
                  <option key={value} value={value}>{value} minutes</option>
                ))}
              </select>
            </label>
            <label>Focus area <small>(optional)</small>
              <input className="field" maxLength={120} value={focus} placeholder="For example, coursework"
                onChange={e => setFocus(e.target.value)} />
            </label>
            <p>Generating sends your objective and selected workspace details to Google Gemini.</p>
            <button className="button-primary" disabled={!objective.trim()} type="submit">
              {result.state === 'loading' ? 'Generating…' : 'Generate plan'}
            </button>
          </fieldset>
        </form>
        {result.state === 'ready' ? <PlanResult plan={result.plan} budget={result.budget} /> : (
          <div className="planning-panel planning-state">
            {result.state === 'loading' ? <p role="status">Reviewing your workspace and drafting a plan…</p>
              : result.state === 'error' ? <div role="alert"><h2>Couldn’t generate a plan</h2>
                <p>{result.message}</p></div>
              : <div><h2>Your plan</h2><p>Generate a plan to see suggested activities, time estimates, and deadline considerations.</p></div>}
          </div>
        )}
      </div>
    </section>
  )
}

function PlanResult({ plan, budget }: { plan: Plan; budget: number }) {
  return (
    <section className="planning-panel planning-result" aria-label="Generated plan">
      <p className="eyebrow" role="status">Plan ready · {plan.total_minutes} of {budget} min</p>
      <h2>{plan.title}</h2>
      <p>{plan.summary}</p>
      <ol>
        {plan.activities.map((activity, index) => (
          <li key={index}>
            <div className="planning-activity"><h3>{activity.title}</h3><span className="badge">{activity.duration_minutes} min</span></div>
            <p>{activity.reason}</p>
            {activity.task && <p className="planning-reference">Task · {activity.task.title}</p>}
            {activity.project && <p className="planning-reference">Project · {activity.project.title}</p>}
          </li>
        ))}
      </ol>
      {plan.deadline_considerations.length > 0 && <div className="planning-deadlines">
        <h3>Deadline considerations</h3>
        <ul>{plan.deadline_considerations.map((item, index) => <li key={index}>{item}</li>)}</ul>
      </div>}
      <p className="planning-note">These are suggestions. Your saved records haven’t changed.</p>
    </section>
  )
}
