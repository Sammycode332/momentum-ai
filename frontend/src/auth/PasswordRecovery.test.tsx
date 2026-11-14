import { afterEach, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
const auth = vi.hoisted(() => ({ requestPasswordReset: vi.fn(), resetPassword: vi.fn() }))
vi.mock('./auth-client', () => ({ authClient: auth }))
import { PasswordRecovery } from './PasswordRecovery'
afterEach(() => { history.replaceState(null, '', '/'); vi.clearAllMocks() })

it('requests a same-origin recovery link without confirming account existence', async () => {
  auth.requestPasswordReset.mockResolvedValue({ error: null })
  render(<PasswordRecovery onBack={() => {}} />)
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'synthetic@example.test' } })
  fireEvent.click(screen.getByRole('button', { name: 'Send recovery link' }))
  await waitFor(() => expect(auth.requestPasswordReset).toHaveBeenCalledWith({ email: 'synthetic@example.test', redirectTo: `${location.origin}/?flow=reset-password` }))
  expect(await screen.findByRole('status')).toHaveTextContent('If this address has an eligible account')
})

it('removes the token from the URL and only submits matching new passwords', async () => {
  history.replaceState(null, '', '/?flow=reset-password&token=synthetic-reset-token')
  auth.resetPassword.mockResolvedValue({ error: null })
  render(<PasswordRecovery onBack={() => {}} />)
  expect(location.search).not.toContain('token')
  fireEvent.change(screen.getByLabelText('New password'), { target: { value: 'synthetic-password' } })
  fireEvent.change(screen.getByLabelText('Confirm new password'), { target: { value: 'different-password' } })
  fireEvent.click(screen.getByRole('button', { name: 'Save new password' }))
  expect(auth.resetPassword).not.toHaveBeenCalled()
  expect(screen.getByRole('alert')).toHaveTextContent('do not match')
  fireEvent.change(screen.getByLabelText('Confirm new password'), { target: { value: 'synthetic-password' } })
  fireEvent.click(screen.getByRole('button', { name: 'Save new password' }))
  await waitFor(() => expect(auth.resetPassword).toHaveBeenCalledWith({ token: 'synthetic-reset-token', newPassword: 'synthetic-password' }))
  expect(await screen.findByRole('status')).toHaveTextContent('Password updated')
})
