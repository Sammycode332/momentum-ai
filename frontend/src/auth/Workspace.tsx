import { useState } from 'react'

import { authClient } from './auth-client'

type WorkspaceProps = {
  email: string
  onSignedOut: () => Promise<void>
}

export function Workspace({ email, onSignedOut }: WorkspaceProps) {
  const [apiStatus, setApiStatus] = useState<string | null>(null)
  const [isCheckingApi, setIsCheckingApi] = useState(false)
  const [isSigningOut, setIsSigningOut] = useState(false)
  const [signOutError, setSignOutError] = useState<string | null>(null)

  async function checkBackendSession() {
    setApiStatus(null)
    setIsCheckingApi(true)
    try {
      const session = await authClient.getSession()
      const token = session.data?.session?.token
      if (!token) {
        setApiStatus('No access token is available for this session.')
        return
      }

      const response = await fetch('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!response.ok) {
        setApiStatus('The backend rejected this session.')
        return
      }
      setApiStatus('The backend verified your session.')
    } catch {
      setApiStatus('The backend verification request could not be completed.')
    } finally {
      setIsCheckingApi(false)
    }
  }

  async function signOut() {
    setSignOutError(null)
    setIsSigningOut(true)
    try {
      const result = await authClient.signOut()
      if (result.error) {
        setSignOutError('Sign out could not be completed. Please try again.')
        return
      }
      await onSignedOut()
    } catch {
      setSignOutError('Sign out could not be completed. Please try again.')
    } finally {
      setIsSigningOut(false)
    }
  }

  return (
    <section className="w-full max-w-xl rounded-xl border border-slate-700 bg-slate-900 p-8 shadow-xl">
      <p className="text-sm font-medium text-cyan-300">Momentum AI workspace</p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight">You’re signed in</h1>
      <p className="mt-4 text-slate-300">{email}</p>
      <div className="mt-6 flex flex-wrap gap-3">
        <button
          className="rounded-md bg-cyan-300 px-4 py-2 font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-60"
          type="button"
          onClick={checkBackendSession}
          disabled={isCheckingApi}
        >
          {isCheckingApi ? 'Checking…' : 'Verify backend session'}
        </button>
        <button
          className="rounded-md border border-slate-500 px-4 py-2 font-semibold text-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
          type="button"
          onClick={signOut}
          disabled={isSigningOut}
        >
          {isSigningOut ? 'Signing out…' : 'Sign out'}
        </button>
      </div>
      {signOutError ? <p role="alert" className="mt-4 text-sm text-rose-300">{signOutError}</p> : null}
      {apiStatus ? <p role="status" className="mt-4 text-sm text-slate-300">{apiStatus}</p> : null}
    </section>
  )
}
