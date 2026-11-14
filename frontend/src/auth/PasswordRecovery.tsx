import { useEffect, useState } from 'react'
import { authClient } from './auth-client'

export function PasswordRecovery({ onBack }: { onBack: () => void }) {
  const [token] = useState(() => new URLSearchParams(location.search).get('token') || '')
  const [email, setEmail] = useState(''), [password, setPassword] = useState(''), [confirmation, setConfirmation] = useState('')
  const [busy, setBusy] = useState(false), [sent, setSent] = useState(false), [done, setDone] = useState(false), [error, setError] = useState('')
  useEffect(() => {
    // Keep a reset credential in component memory only, never storage or the visible URL.
    const url = new URL(location.href)
    url.searchParams.delete('token'); url.searchParams.delete('error')
    history.replaceState(history.state, '', url)
  }, [])
  return <section className="auth-card"><p className="eyebrow">Momentum AI</p><h1>{token ? 'Choose a new password' : 'Reset your password'}</h1><p className="auth-copy">{token ? 'Enter your new password twice to confirm it.' : 'We’ll send a recovery link if this email has an eligible account.'}</p>
    {!done && <form className="auth-form" onSubmit={async e => {
      e.preventDefault(); setError('')
      if (token && password !== confirmation) { setError('Your passwords do not match.'); return }
      setBusy(true)
      try {
        const result = token ? await authClient.resetPassword({ token, newPassword: password }) : await authClient.requestPasswordReset({ email: email.trim(), redirectTo: `${location.origin}/?flow=reset-password` })
        if (result.error) throw new Error('Recovery failed')
        if (token) { setDone(true); setPassword(''); setConfirmation('') } else setSent(true)
      } catch { setError(token ? 'This reset link could not be used. It may have expired. Request a new link and try again.' : 'Recovery is unavailable right now. Try again later.') }
      finally { setBusy(false) }
    }}>{token ? <><label>New password<input className="field" type="password" autoComplete="new-password" minLength={8} maxLength={256} required value={password} onChange={e => setPassword(e.target.value)} disabled={busy} /></label><label>Confirm new password<input className="field" type="password" autoComplete="new-password" minLength={8} maxLength={256} required value={confirmation} onChange={e => setConfirmation(e.target.value)} disabled={busy} /></label></> : <label>Email<input className="field" type="email" autoComplete="email" required value={email} onChange={e => { setEmail(e.target.value); setSent(false) }} disabled={busy} /></label>}
      <button className="button-primary wide" disabled={busy || (!token && sent)}>{busy ? 'Working…' : token ? 'Save new password' : 'Send recovery link'}</button></form>}
    {sent && <p role="status" className="auth-copy">If this address has an eligible account, you’ll receive a link. Check your inbox and spam folder.</p>}{done && <p role="status" className="feedback-success">Password updated. You can sign in with your new password.</p>}{error && <p role="alert" className="feedback-error">{error}</p>}
    <button className="text-button auth-link" disabled={busy} onClick={() => { const url = new URL(location.href); url.searchParams.delete('flow'); history.replaceState(history.state, '', url); onBack() }}>Back to sign in</button>
  </section>
}
