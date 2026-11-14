import { useState } from 'react'
import type { FormEvent } from 'react'

import { authClient } from './auth-client'
import { PasswordRecovery } from './PasswordRecovery'

type AuthMode = 'sign-in' | 'sign-up' | 'verify-email'

type AuthFormProps = {
  onAuthenticated: () => Promise<void>
  sessionError?: boolean
}

function errorCode(error: unknown): string | undefined {
  if (error && typeof error === 'object' && 'code' in error && typeof error.code === 'string') {
    return error.code
  }
  return undefined
}

function errorMessage(error: unknown): string {
  if (errorCode(error) === 'EMAIL_NOT_VERIFIED') {
    return 'Verify your email before signing in.'
  }
  if (errorCode(error) === 'OTP_EXPIRED') {
    return 'This verification code has expired. Request a new code and try again.'
  }
  if (errorCode(error) === 'INVALID_OTP') {
    return 'That verification code is invalid. Try again or request a new code.'
  }
  if (errorCode(error) === 'TOO_MANY_ATTEMPTS') {
    return 'Too many verification attempts. Request a new code and try again.'
  }
  if (
    error &&
    typeof error === 'object' &&
    'message' in error &&
    typeof error.message === 'string'
  ) {
    return error.message
  }
  return 'Authentication could not be completed. Please try again.'
}

export function AuthForm({ onAuthenticated, sessionError = false }: AuthFormProps) {
  const [recovery, setRecovery] = useState(() => new URLSearchParams(location.search).get('flow') === 'reset-password')
  const [mode, setMode] = useState<AuthMode>('sign-in')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [verificationCode, setVerificationCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isResending, setIsResending] = useState(false)

  async function requestVerificationCode(address: string) {
    const result = await authClient.emailOtp.sendVerificationOtp({
      email: address,
      type: 'email-verification',
    })
    if (result.error) {
      throw result.error
    }
  }

  function showVerificationPrompt(address: string) {
    setEmail(address)
    setPassword('')
    setVerificationCode('')
    setMode('verify-email')
    setNotice('Check your email for the verification code, then enter it below.')
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setNotice(null)

    if (mode === 'verify-email') {
      await verifyEmail()
      return
    }

    if (!email.trim()) {
      setError('Enter your email address.')
      return
    }
    if (password.length < 8) {
      setError('Use a password with at least 8 characters.')
      return
    }

    setIsSubmitting(true)
    try {
      const result =
        mode === 'sign-in'
          ? await authClient.signIn.email({ email, password })
          : await authClient.signUp.email({
              email,
              password,
              name: email,
            })

      if (result.error) {
        if (errorCode(result.error) === 'EMAIL_NOT_VERIFIED') {
          showVerificationPrompt(email)
          return
        }
        setError(errorMessage(result.error))
        return
      }

      if (mode === 'sign-in') {
        await onAuthenticated()
      } else {
        showVerificationPrompt(email)
      }
    } catch (authError) {
      if (errorCode(authError) === 'EMAIL_NOT_VERIFIED') {
        showVerificationPrompt(email)
        return
      }
      setError(errorMessage(authError))
    } finally {
      setIsSubmitting(false)
    }
  }

  async function verifyEmail() {
    setError(null)
    setNotice(null)

    if (!verificationCode.trim()) {
      setError('Enter the verification code from your email.')
      return
    }

    setIsSubmitting(true)
    try {
      const result = await authClient.emailOtp.verifyEmail({
        email,
        otp: verificationCode.trim(),
      })
      if (result.error) {
        setError(errorMessage(result.error))
        return
      }

      setVerificationCode('')
      setPassword('')
      setMode('sign-in')
      setNotice('Email verified. Sign in with your email and password.')
      await onAuthenticated()
    } catch (authError) {
      setError(errorMessage(authError))
    } finally {
      setIsSubmitting(false)
    }
  }

  async function resendVerificationCode() {
    if (!email) {
      return
    }

    setError(null)
    setNotice(null)
    setIsResending(true)
    try {
      await requestVerificationCode(email)
      setVerificationCode('')
      setNotice('A new verification code was sent. Check your email and enter the new code.')
    } catch (authError) {
      setError(errorMessage(authError))
    } finally {
      setIsResending(false)
    }
  }

  if (recovery) return <PasswordRecovery onBack={() => setRecovery(false)} />

  return (
    <section className="auth-card">
      <p className="eyebrow">Momentum AI</p>
      <h1>
        {mode === 'sign-in'
          ? 'Welcome back'
          : mode === 'sign-up'
            ? 'Create your workspace'
            : 'Verify your email'}
      </h1>
      <p className="auth-copy">
        {mode === 'sign-in'
          ? 'Sign in to continue your Momentum AI journey.'
          : mode === 'sign-up'
            ? 'Start with an email and password.'
            : 'Enter your account email and the verification code you received.'}
      </p>

      {sessionError ? (
        <p role="alert" className="feedback-error">
          Your session could not be restored. Sign in again and verify that this browser origin is trusted in Neon Auth.
        </p>
      ) : null}

      {mode !== 'verify-email' && import.meta.env.VITE_GOOGLE_SIGN_IN_ENABLED === 'true' && <button className="button-secondary wide auth-link" disabled={isSubmitting} onClick={async () => {
        setIsSubmitting(true); setError(null)
        try { const result = await authClient.signIn.social({ provider: 'google', callbackURL: location.origin }); if (result.error) throw new Error('OAuth failed') }
        catch { setError('Google sign-in is unavailable. Try email sign-in instead.') }
        finally { setIsSubmitting(false) }
      }}>Continue with Google</button>}
      <form className="auth-form" onSubmit={submit}>
        <label>
          Email
          <input
            className="field"
            type="email"
            autoComplete="email"
            required={mode === 'verify-email'}
            value={email}
            onChange={(event) => {
              setEmail(event.target.value)
              setVerificationCode('')
            }}
            disabled={isSubmitting || isResending}
          />
        </label>
        {mode === 'verify-email' ? (
          <label>
            Verification code
            <input
              className="field"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              value={verificationCode}
              onChange={(event) => setVerificationCode(event.target.value)}
              disabled={isSubmitting || isResending}
            />
          </label>
        ) : (
            <label>
              Password
              <input
                className="field"
                type="password"
                autoComplete={mode === 'sign-in' ? 'current-password' : 'new-password'}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                disabled={isSubmitting}
              />
            </label>
        )}
        {error ? <p role="alert" className="feedback-error">{error}</p> : null}
        {notice ? <p role="status" className="feedback-success">{notice}</p> : null}
        <button
          className="button-primary wide"
          type="submit"
          disabled={isSubmitting || isResending}
        >
          {isSubmitting
            ? 'Working…'
            : mode === 'sign-in'
              ? 'Sign in'
              : mode === 'sign-up'
                ? 'Create account'
                : 'Verify email'}
        </button>
        {mode === 'verify-email' ? (
          <button
            className="text-button"
            type="button"
            onClick={(event) => {
              if (event.currentTarget.form?.reportValidity()) {
                void resendVerificationCode()
              }
            }}
            disabled={isSubmitting || isResending}
          >
            {isResending ? 'Sending code…' : 'Resend verification code'}
          </button>
        ) : null}
      </form>

      {mode === 'sign-in' && <button className="text-button auth-link" disabled={isSubmitting} onClick={() => { setPassword(''); setRecovery(true) }}>Forgot password?</button>}

      {mode === 'sign-in' ? (
        <button
          className="text-button auth-link"
          type="button"
          onClick={() => {
            setError(null)
            setNotice(null)
            setPassword('')
            setMode('verify-email')
          }}
          disabled={isSubmitting}
        >
          I have a verification code
        </button>
      ) : null}

      <button
        className="text-button auth-link"
        type="button"
        onClick={() => {
          setMode(mode === 'sign-in' ? 'sign-up' : 'sign-in')
          setError(null)
          setNotice(null)
          setVerificationCode('')
        }}
        disabled={isSubmitting || isResending}
      >
        {mode === 'sign-in'
          ? 'Need an account? Create one'
          : mode === 'sign-up'
            ? 'Already have an account? Sign in'
            : 'Back to sign in'}
      </button>
    </section>
  )
}
