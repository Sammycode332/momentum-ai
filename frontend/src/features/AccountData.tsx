import { useEffect, useRef, useState } from 'react'
import { api, errorText } from './api'

export function AccountData() {
  const [busy, setBusy] = useState(false), [message, setMessage] = useState(''), [error, setError] = useState('')
  const controller = useRef<AbortController | null>(null)
  useEffect(() => () => controller.current?.abort(), [])
  const contact = import.meta.env.VITE_SUPPORT_EMAIL?.trim()
  const validContact = typeof contact === 'string' && /^[^\s@?&#]+@[^\s@?&#]+\.[^\s@?&#]+$/.test(contact)
  async function download() {
    const current = new AbortController(); controller.current = current
    setBusy(true); setError(''); setMessage('Preparing your export…')
    try {
      const manifest = await api<{ sections: string[]; notice: string }>('account/export', 'GET', undefined, current.signal)
      const data: Record<string, unknown[]> = {}; const started = new Date().toISOString(); let bytes = 0
      for (const section of manifest.sections) {
        data[section] = []; let offset: number | null = 0
        do {
          setMessage(`Exporting ${section}…`)
          const page: { items: unknown[]; next_offset: number | null } = await api(`account/export/${encodeURIComponent(section)}?offset=${offset}`, 'GET', undefined, current.signal)
          bytes += new TextEncoder().encode(JSON.stringify(page.items)).length
          if (bytes > 25_000_000) throw new Error('This export exceeds the browser download limit. Contact support for a larger export. No partial file was downloaded.')
          data[section].push(...page.items); offset = page.next_offset
        } while (offset !== null)
      }
      current.signal.throwIfAborted()
      const blob = new Blob([JSON.stringify({ version: 1, started_at: started, finished_at: new Date().toISOString(), notice: manifest.notice, data }, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob), link = document.createElement('a')
      link.href = url; link.download = `momentum-export-${started.slice(0, 10)}.json`; link.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
      setMessage('Your export is ready. Store the downloaded file somewhere private.')
    } catch (e) { if (!current.signal.aborted) { setError(errorText(e)); setMessage('') } }
    finally { if (controller.current === current) { if (!current.signal.aborted) setBusy(false); controller.current = null } }
  }
  return <div className="feature-page"><section className="feature-card"><h2>Your data</h2><p>Download your goals, records, conversations, practice sessions, approved memories and notification history as JSON. Passwords, tokens and push credentials are excluded.</p><p className="state-copy">Avoid editing your workspace during the export. This download is assembled in pages, so simultaneous changes can affect consistency.</p><div className="feature-actions"><button className="primary-button" disabled={busy} onClick={() => void download()}>{busy ? 'Preparing export…' : 'Download my data'}</button>{busy && <button onClick={() => { controller.current?.abort(); setBusy(false); setMessage('Export cancelled. No partial file was downloaded.') }}>Cancel</button>}</div>{message && <p role="status">{message}</p>}{error && <p role="alert" className="notice-error">{error}</p>}</section><section className="feature-card"><h2>Support & feedback</h2>{validContact ? <p><a href={`mailto:${contact}?subject=Momentum%20AI%20support`}>Contact support or send feedback</a>. Please do not include passwords, tokens or private conversation exports.</p> : <p>The operator has not configured a support contact yet.</p>}<h3>Account deletion</h3><p>You can delete individual records, chats, memories and practice sessions in the workspace. Full account deletion, including the Neon sign-in identity and retention handling, is not available yet.</p></section></div>
}
