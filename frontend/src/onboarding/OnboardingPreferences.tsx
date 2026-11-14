import { useEffect, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'

import { loadOnboarding, saveOnboarding, skipOnboarding } from './onboarding-api'
import type { Onboarding, Preferences } from './onboarding-api'

const inputClass = 'field'
const emptyPreferences: Preferences = { primary_focus: '', current_goals: '', planning_time: '' }

export function OnboardingPreferences({ children }: { children: ReactNode }) {
  const [record, setRecord] = useState<Onboarding | null | undefined>(undefined)
  const [loadError, setLoadError] = useState(false)
  const [loadErrorMessage, setLoadErrorMessage] = useState('')
  const [loadAttempt, setLoadAttempt] = useState(0)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(emptyPreferences)
  const [busy, setBusy] = useState(false)
  const [feedback, setFeedback] = useState<'saved' | 'error' | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    loadOnboarding(controller.signal).then(
      (result) => {
        if (!controller.signal.aborted) setRecord(result)
      },
      (error) => {
        if (!controller.signal.aborted) {
          setLoadErrorMessage(error instanceof Error ? error.message : 'Planning preferences are temporarily unavailable.')
          setLoadError(true)
        }
      },
    )
    return () => controller.abort()
  }, [loadAttempt])

  async function persist(action: () => Promise<Onboarding>) {
    if (busy) return
    setBusy(true)
    setFeedback(null)
    try {
      const result = await action()
      setRecord(result)
      setEditing(false)
      if (result.status === 'completed') setFeedback('saved')
    } catch {
      setFeedback('error')
    } finally {
      setBusy(false)
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void persist(() => saveOnboarding({
      primary_focus: draft.primary_focus.trim(),
      current_goals: draft.current_goals.trim(),
      planning_time: draft.planning_time,
    }))
  }

  if (record === undefined) {
    if (!loadError) return <p role="status" className="state-copy">Loading onboarding preferences…</p>
    return (
      <>
        <p role="alert" className="feedback-error">Could not load onboarding preferences. {loadErrorMessage}</p>
        <button type="button" className="text-button" onClick={() => {
          setLoadError(false)
          setLoadErrorMessage('')
          setLoadAttempt((attempt) => attempt + 1)
        }}>Retry preferences</button>
        {children}
      </>
    )
  }

  const showForm = record === null || editing
  return (
    <>
      <section className="settings-panel" aria-labelledby="onboarding-title">
        <h2 id="onboarding-title">
          {record === null ? 'Set up your workspace' : 'Planning preferences'}
        </h2>
        {showForm ? (
          <form onSubmit={submit} className="preferences-form">
            <fieldset disabled={busy}>
              <label>
                Primary focus
                <input className={inputClass} value={draft.primary_focus} maxLength={120} required
                  onChange={(event) => setDraft({ ...draft, primary_focus: event.target.value })} />
              </label>
              <label>
                Current goals
                <textarea className={inputClass} value={draft.current_goals} maxLength={1000} required
                  onChange={(event) => setDraft({ ...draft, current_goals: event.target.value })} />
              </label>
              <label>
                Preferred daily planning time
                <input className={inputClass} type="time" value={draft.planning_time} required
                  onChange={(event) => setDraft({ ...draft, planning_time: event.target.value })} />
              </label>
              <div className="inline-form">
                <button type="submit" className="button-primary"
                  disabled={!draft.primary_focus.trim() || !draft.current_goals.trim() || !draft.planning_time}>
                  {busy ? 'Saving…' : 'Save preferences'}
                </button>
                {record === null ? (
                  <button type="button" className="button-secondary" onClick={() => void persist(skipOnboarding)}>Skip for now</button>
                ) : (
                  <button type="button" className="button-secondary" onClick={() => {
                    setEditing(false)
                    setFeedback(null)
                  }}>Cancel</button>
                )}
              </div>
            </fieldset>
          </form>
        ) : (
          <>
            {record.status === 'completed' && (
              <dl className="preference-summary">
                <div><dt>Primary focus</dt><dd className="break-words">{record.primary_focus}</dd></div>
                <div><dt>Current goals</dt><dd className="whitespace-pre-wrap break-words">{record.current_goals}</dd></div>
                <div><dt>Preferred daily planning time</dt><dd>{record.planning_time}</dd></div>
              </dl>
            )}
            <button type="button" className="text-button" onClick={() => {
              setDraft(record.status === 'completed' ? {
                primary_focus: record.primary_focus,
                current_goals: record.current_goals,
                planning_time: record.planning_time,
              } : emptyPreferences)
              setFeedback(null)
              setEditing(true)
            }}>{record.status === 'completed' ? 'Edit preferences' : 'Set planning preferences'}</button>
          </>
        )}
        {feedback === 'error' && <p role="alert" className="feedback-error">Could not save onboarding. Try again.</p>}
        {feedback === 'saved' && <p role="status" className="feedback-success">Preferences saved.</p>}
      </section>
      {record !== null && children}
    </>
  )
}
