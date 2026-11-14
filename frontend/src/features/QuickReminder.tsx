import { useRef, useState } from 'react'
import { Modal } from './Modal'
import { api, errorText } from './api'

function initialTime(date?: string | null) {
  const candidate = date ? new Date(`${date}T09:00:00`) : new Date(Date.now() + 3600000)
  const value = Number.isFinite(candidate.getTime()) && candidate.getTime() > Date.now() ? candidate : new Date(Date.now() + 3600000)
  return new Date(value.getTime() - value.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
}
export function QuickReminder({ title, date, onClose, onSaved }: { title: string; date?: string | null; onClose: () => void; onSaved: () => void }) {
  const [name, setName] = useState(title.slice(0, 200)), [due, setDue] = useState(() => initialTime(date)), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const request = useRef({ key: '', id: '' })
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone
  return <Modal title="Schedule a reminder" onClose={onClose} busy={busy}><form className="feature-form" onSubmit={async e => {
    e.preventDefault(); setError(''); const when = new Date(due)
    if (!Number.isFinite(when.getTime()) || when.getTime() <= Date.now()) { setError('Choose a future date and time.'); return }
    const body = { title: name, due_at: when.toISOString(), timezone, repeat: 'none' }
    const key = JSON.stringify(body); if (request.current.key !== key) request.current = { key, id: crypto.randomUUID() }
    setBusy(true)
    try { await api('reminders', 'POST', { ...body, id: request.current.id }); onSaved() } catch (failure) { setError(errorText(failure)) } finally { setBusy(false) }
  }}><label>Reminder title<input className="field" required maxLength={200} value={name} onChange={e => setName(e.target.value)} disabled={busy} /></label><label>Date and time ({timezone})<input className="field" type="datetime-local" required value={due} onChange={e => setDue(e.target.value)} disabled={busy} /></label><p className="state-copy">This creates a separate reminder. If the record changes, reschedule or cancel it in Notifications. Delivery depends on the reminder service and your preferences.</p>{error && <p role="alert" className="notice-error">{error}</p>}<div className="dialog-actions"><button type="button" className="button-secondary" disabled={busy} onClick={onClose}>Cancel</button><button className="button-primary" disabled={busy}>{busy ? 'Saving…' : 'Schedule reminder'}</button></div></form></Modal>
}
