import { useState } from 'react'
import { api, errorText } from './api'
import { Modal } from './Modal'
export function MessageTools({ content }: { content: string }) {
  const [mode, setMode] = useState<'memory' | 'action' | null>(null), [draft, setDraft] = useState(''), [busy, setBusy] = useState(false), [error, setError] = useState(''), [notice, setNotice] = useState('')
  function open(next: 'memory' | 'action') { setMode(next); setDraft(content.slice(0, next === 'memory' ? 500 : 2000)); setError(''); setNotice('') }
  return <><details className="message-tools"><summary>Use this response</summary><div className="feature-actions"><button className="text-button" onClick={async () => { try { await navigator.clipboard.writeText(content); setNotice('Copied.'); setError('') } catch { setError('Copy was unavailable. Select the text to copy it manually.') } }}>Copy</button><button className="text-button" onClick={() => open('memory')}>Propose a memory</button><button className="text-button" onClick={() => open('action')}>Propose an action</button></div>{notice && <p role="status">{notice}</p>}{error && !mode && <p role="alert">{error}</p>}</details>{mode && <Modal title={mode === 'memory' ? 'Review a memory proposal' : 'Describe the proposed action'} busy={busy} onClose={() => setMode(null)}><form className="feature-form" onSubmit={async e => {
    e.preventDefault(); setBusy(true); setError('')
    try {
      if (mode === 'memory') { await api('memory', 'POST', { content: draft }); setNotice('Memory proposed. Review and approve it in Settings → AI memory & privacy before it is used.') }
      else { await api('actions/suggest', 'POST', { instruction: draft }); setNotice('Action proposed. Open the Approvals tab to review the exact change. Nothing has been applied.') }
      setMode(null)
    } catch (failure) { setError(errorText(failure)) } finally { setBusy(false) }
  }}><p className="state-copy">{mode === 'memory' ? 'Keep only a useful preference or fact about you. Correct the text below; it may be shortened. This saves a pending proposal, not an approved memory.' : 'Describe one concrete change. Gemini will prepare a proposal for a separate approval; this does not execute a change.'}</p><label>{mode === 'memory' ? 'Proposed memory' : 'Requested change'}<textarea className="field" rows={6} required maxLength={mode === 'memory' ? 500 : 2000} value={draft} onChange={e => setDraft(e.target.value)} disabled={busy} /></label>{error && <p role="alert" className="notice-error">{error}</p>}<div className="dialog-actions"><button type="button" className="button-secondary" disabled={busy} onClick={() => setMode(null)}>Cancel</button><button className="button-primary" disabled={busy || !draft.trim()}>{busy ? 'Preparing…' : 'Create proposal'}</button></div></form></Modal>}</>
}
