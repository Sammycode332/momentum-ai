import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('./goals/goals-api', () => ({ listGoals: vi.fn().mockResolvedValue([]) }))
vi.mock('./features/api', async importOriginal => ({
  ...await importOriginal<typeof import('./features/api')>(),
  api: vi.fn().mockResolvedValue([]),
}))

const authMocks = vi.hoisted(() => ({
  getSession: vi.fn(),
  signIn: vi.fn(),
  signOut: vi.fn(),
  signUp: vi.fn(),
  sendVerificationOtp: vi.fn(),
  verifyEmail: vi.fn(),
  useSession: vi.fn(),
  refetch: vi.fn(),
  loadOnboarding: vi.fn(),
  saveOnboarding: vi.fn(),
  skipOnboarding: vi.fn(),
  listRecords: vi.fn(),
}))

vi.mock('./records/records-api', async importOriginal => ({
  ...await importOriginal<typeof import('./records/records-api')>(),
  listRecords: authMocks.listRecords,
}))

vi.mock('./onboarding/onboarding-api', () => ({
  loadOnboarding: authMocks.loadOnboarding,
  saveOnboarding: authMocks.saveOnboarding,
  skipOnboarding: authMocks.skipOnboarding,
}))

vi.mock('./auth/auth-client', () => ({
  authClient: {
    getSession: authMocks.getSession,
    signIn: { email: authMocks.signIn },
    signOut: authMocks.signOut,
    signUp: { email: authMocks.signUp },
    emailOtp: {
      sendVerificationOtp: authMocks.sendVerificationOtp,
      verifyEmail: authMocks.verifyEmail,
    },
    useSession: authMocks.useSession,
  },
}))

import App from './App'

const skipped = {
  status: 'skipped', primary_focus: null, current_goals: null, planning_time: null,
}

describe('App', () => {
  beforeEach(() => {
    authMocks.listRecords.mockReset().mockResolvedValue([])
    authMocks.loadOnboarding.mockReset()
    authMocks.loadOnboarding.mockResolvedValue(skipped)
    authMocks.saveOnboarding.mockReset()
    authMocks.skipOnboarding.mockReset()
    authMocks.getSession.mockReset()
    authMocks.signIn.mockReset()
    authMocks.signOut.mockReset()
    authMocks.signUp.mockReset()
    authMocks.sendVerificationOtp.mockReset()
    authMocks.verifyEmail.mockReset()
    authMocks.useSession.mockReset()
    authMocks.refetch.mockReset()
    authMocks.refetch.mockResolvedValue(undefined)
    authMocks.useSession.mockReturnValue({
      data: null,
      error: null,
      isPending: false,
      refetch: authMocks.refetch,
    })
  })

  it.each(['returned', 'thrown'])('shows a safe recoverable sign-out error when %s', async failure => {
    authMocks.useSession.mockReturnValue({
      data: { user: { email: 'person@example.test' } },
      isPending: false, refetch: authMocks.refetch,
    })
    if (failure === 'returned') authMocks.signOut.mockResolvedValueOnce({ error: { message: 'private details' } })
    else authMocks.signOut.mockRejectedValueOnce(new Error('private details'))
    authMocks.signOut.mockResolvedValueOnce({ error: null })
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Sign out' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Could not sign out. Please try again.')
    expect(screen.queryByText('private details')).not.toBeInTheDocument()
    expect(authMocks.refetch).not.toHaveBeenCalled()
    fireEvent.click(screen.getByRole('button', { name: 'Sign out' }))
    await waitFor(() => expect(authMocks.refetch).toHaveBeenCalledOnce())
  })

  it('renders the sign-in experience when there is no session', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', { name: 'Welcome back' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument()
  })

  it('renders a loading state while Neon Auth restores the session', () => {
    authMocks.useSession.mockReturnValue({
      data: null,
      error: null,
      isPending: true,
      refetch: authMocks.refetch,
    })

    render(<App />)

    expect(screen.getByRole('status')).toHaveTextContent('Restoring your session…')
    expect(authMocks.listRecords).not.toHaveBeenCalled()
    expect(screen.queryByRole('button', { name: 'Sign in' })).not.toBeInTheDocument()
  })

  it('restores the workspace from an existing session', () => {
    authMocks.useSession.mockReturnValue({
      data: { user: { email: 'person@example.test' } },
      error: null,
      isPending: false,
      refetch: authMocks.refetch,
    })

    render(<App />)

    expect(
      screen.getByRole('heading', { name: 'Welcome to Momentum' }),
    ).toBeInTheDocument()
    expect(screen.getByText('person@example.test')).toBeInTheDocument()
  })

  it.each([
    ['+ New task', 'Create task'],
    ['New project', 'Create project'],
  ])('opens the existing create form from the Overview %s action', async (action, form) => {
    authMocks.useSession.mockReturnValue({
      data: { user: { email: 'person@example.test', name: 'Maya' } },
      isPending: false,
      refetch: authMocks.refetch,
    })
    render(<App />)
    expect(screen.getByRole('heading', { name: 'Welcome, Maya' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: action }))
    expect(await screen.findByRole('form', { name: form })).toBeInTheDocument()
  })

  it('persists skipping onboarding in Settings', async () => {
    authMocks.useSession.mockReturnValue({
      data: { user: { id: 'test-user', email: 'person@example.test' } },
      isPending: false,
      refetch: authMocks.refetch,
    })
    authMocks.loadOnboarding.mockResolvedValueOnce(skipped).mockResolvedValueOnce(null)
    authMocks.skipOnboarding.mockResolvedValue(skipped)
    const first = render(<App />)

    fireEvent.click(screen.getByRole('button', { name: 'Settings' }))
    expect(await screen.findByRole('heading', { name: 'Set up your workspace' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Skip for now' }))
    expect(await screen.findByRole('button', { name: 'Set planning preferences' })).toBeInTheDocument()
    expect(authMocks.skipOnboarding).toHaveBeenCalledOnce()

    first.unmount()
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Settings' }))
    expect(await screen.findByRole('button', { name: 'Set planning preferences' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Skip for now' })).not.toBeInTheDocument()
  })

  it('saves onboarding and lets users view and edit the saved fields', async () => {
    authMocks.useSession.mockReturnValue({
      data: { user: { id: 'test-user', email: 'person@example.test' } },
      isPending: false,
      refetch: authMocks.refetch,
    })
    authMocks.loadOnboarding.mockResolvedValue(null)
    const fields = { primary_focus: 'Study', current_goals: 'Finish chapter one', planning_time: '08:30' }
    authMocks.saveOnboarding
      .mockResolvedValueOnce({ status: 'completed', ...fields })
      .mockResolvedValueOnce({ status: 'completed', ...fields, planning_time: '09:00' })
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Settings' }))

    fireEvent.change(await screen.findByLabelText('Primary focus'), { target: { value: fields.primary_focus } })
    fireEvent.change(screen.getByLabelText('Current goals'), { target: { value: fields.current_goals } })
    fireEvent.change(screen.getByLabelText('Preferred daily planning time'), { target: { value: fields.planning_time } })
    fireEvent.click(screen.getByRole('button', { name: 'Save preferences' }))
    expect(await screen.findByText('Preferences saved.')).toBeInTheDocument()
    expect(screen.getByText(fields.current_goals)).toBeInTheDocument()
    expect(authMocks.saveOnboarding).toHaveBeenCalledWith(fields)

    fireEvent.click(screen.getByRole('button', { name: 'Edit preferences' }))
    expect(screen.getByLabelText('Primary focus')).toHaveValue(fields.primary_focus)
    fireEvent.change(screen.getByLabelText('Preferred daily planning time'), { target: { value: '09:00' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save preferences' }))
    expect(await screen.findByText('09:00')).toBeInTheDocument()
    expect(authMocks.saveOnboarding).toHaveBeenLastCalledWith({ ...fields, planning_time: '09:00' })
  })

  it('shows a retryable Settings error when onboarding preferences cannot load', async () => {
    authMocks.useSession.mockReturnValue({
      data: { user: { id: 'test-user', email: 'person@example.test' } },
      isPending: false,
      refetch: authMocks.refetch,
    })
    authMocks.loadOnboarding.mockResolvedValueOnce(skipped).mockRejectedValueOnce(new Error('Offline'))
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Settings' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load onboarding preferences.')
    fireEvent.click(screen.getByRole('button', { name: 'Retry preferences' }))
    expect(await screen.findByRole('button', { name: 'Set planning preferences' })).toBeInTheDocument()
  })

  it('validates a short password before calling Neon Auth', () => {
    render(<App />)

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'person@example.test' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'short' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(
      screen.getByText('Use a password with at least 8 characters.'),
    ).toBeInTheDocument()
    expect(authMocks.signIn).not.toHaveBeenCalled()
  })

  it('revalidates the Neon Auth session after sign-in', async () => {
    authMocks.signIn.mockResolvedValue({ data: {}, error: null })
    render(<App />)

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'person@example.test' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    await waitFor(() => expect(authMocks.refetch).toHaveBeenCalledOnce())
  })

  it('shows a safe provider error for invalid login credentials', async () => {
    authMocks.signIn.mockResolvedValue({
      data: null,
      error: { message: 'Invalid email or password.' },
    })
    render(<App />)

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'person@example.test' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password.')
    expect(authMocks.refetch).not.toHaveBeenCalled()
  })

  it('lets an existing user enter an emailed code directly from the sign-in screen', async () => {
    authMocks.verifyEmail.mockResolvedValue({ data: { status: true }, error: null })
    render(<App />)

    fireEvent.click(screen.getByRole('button', { name: 'I have a verification code' }))
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'person@example.test' },
    })
    fireEvent.change(screen.getByLabelText('Verification code'), {
      target: { value: '123456' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Verify email' }))

    expect(await screen.findByRole('heading', { name: 'Welcome back' })).toBeInTheDocument()
    expect(authMocks.verifyEmail).toHaveBeenCalledWith({
      email: 'person@example.test',
      otp: '123456',
    })
    expect(authMocks.signIn).not.toHaveBeenCalled()
  })

  it('takes an unverified user to the code screen and resends an OTP', async () => {
    authMocks.signIn.mockResolvedValue({
      data: null,
      error: { code: 'EMAIL_NOT_VERIFIED', message: 'Email not verified' },
    })
    authMocks.sendVerificationOtp.mockResolvedValue({ data: { status: true }, error: null })
    render(<App />)

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'person@example.test' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('heading', { name: 'Verify your email' })).toBeInTheDocument()
    expect(screen.getByLabelText('Verification code')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Resend verification code' }))

    await waitFor(() => {
      expect(authMocks.sendVerificationOtp).toHaveBeenCalledWith({
        email: 'person@example.test',
        type: 'email-verification',
      })
    })
    expect(screen.getByRole('status')).toHaveTextContent('A new verification code was sent.')
  })

  it('shows the code screen after sign-up without assuming a session exists', async () => {
    authMocks.signUp.mockResolvedValue({ data: {}, error: null })
    render(<App />)

    fireEvent.click(screen.getByRole('button', { name: 'Need an account? Create one' }))
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'person@example.test' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))

    await waitFor(() => {
      expect(authMocks.signUp).toHaveBeenCalledWith({
        email: 'person@example.test',
        password: 'password123',
        name: 'person@example.test',
      })
    })
    expect(authMocks.refetch).not.toHaveBeenCalled()
    expect(screen.getByRole('heading', { name: 'Verify your email' })).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent(
      'Check your email for the verification code',
    )
    expect(screen.getByRole('button', { name: 'Resend verification code' })).toBeInTheDocument()
  })

  it('verifies an OTP, revalidates a possible automatic session, and returns to sign-in', async () => {
    authMocks.signUp.mockResolvedValue({ data: {}, error: null })
    authMocks.verifyEmail.mockResolvedValue({
      data: { status: true, token: null, user: {} },
      error: null,
    })
    render(<App />)

    fireEvent.click(screen.getByRole('button', { name: 'Need an account? Create one' }))
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'person@example.test' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
    await screen.findByRole('heading', { name: 'Verify your email' })

    fireEvent.change(screen.getByLabelText('Verification code'), {
      target: { value: '123456' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Verify email' }))

    await waitFor(() => {
      expect(authMocks.verifyEmail).toHaveBeenCalledWith({
        email: 'person@example.test',
        otp: '123456',
      })
    })
    expect(authMocks.refetch).toHaveBeenCalledOnce()
    expect(screen.getByRole('heading', { name: 'Welcome back' })).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent(
      'Email verified. Sign in with your email and password.',
    )
  })

  it('shows a safe OTP expiration error', async () => {
    authMocks.signUp.mockResolvedValue({ data: {}, error: null })
    authMocks.verifyEmail.mockResolvedValue({
      data: null,
      error: { code: 'OTP_EXPIRED', message: 'OTP expired' },
    })
    render(<App />)

    fireEvent.click(screen.getByRole('button', { name: 'Need an account? Create one' }))
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'person@example.test' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
    await screen.findByRole('heading', { name: 'Verify your email' })

    fireEvent.change(screen.getByLabelText('Verification code'), {
      target: { value: '123456' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Verify email' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'This verification code has expired. Request a new code and try again.',
    )
  })

  it('shows a safe resend error', async () => {
    authMocks.signIn.mockResolvedValue({
      data: null,
      error: { code: 'EMAIL_NOT_VERIFIED', message: 'Email not verified' },
    })
    authMocks.sendVerificationOtp.mockResolvedValue({
      data: null,
      error: { code: 'TOO_MANY_ATTEMPTS', message: 'Too many attempts' },
    })
    render(<App />)

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'person@example.test' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    await screen.findByRole('heading', { name: 'Verify your email' })

    fireEvent.click(screen.getByRole('button', { name: 'Resend verification code' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Too many verification attempts. Request a new code and try again.',
    )
  })

  it('shows a safe provider error for duplicate registration', async () => {
    authMocks.signUp.mockResolvedValue({
      data: null,
      error: { message: 'An account already exists for this email.' },
    })
    render(<App />)

    fireEvent.click(screen.getByRole('button', { name: 'Need an account? Create one' }))
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'person@example.test' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'An account already exists for this email.',
    )
    expect(authMocks.refetch).not.toHaveBeenCalled()
  })

  it('signs out from the restored workspace', async () => {
    authMocks.useSession.mockReturnValue({
      data: { user: { email: 'person@example.test' } },
      error: null,
      isPending: false,
      refetch: authMocks.refetch,
    })
    authMocks.signOut.mockResolvedValue({ data: {}, error: null })
    render(<App />)

    fireEvent.click(screen.getByRole('button', { name: 'Sign out' }))

    await waitFor(() => expect(authMocks.signOut).toHaveBeenCalledOnce())
    expect(authMocks.refetch).toHaveBeenCalledOnce()
  })
})
