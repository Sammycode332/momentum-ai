import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { api } from './api'
import { PushSettings } from './PushSettings'

vi.mock('./api', () => ({
  api: vi.fn(),
  errorText: (error: Error) => error.message,
}))

afterEach(() => {
  vi.unstubAllGlobals()
  vi.clearAllMocks()
})

it('registers this device and reports push service acceptance', async () => {
  const requestPermission = vi.fn().mockResolvedValue('granted')
  const subscription = {
    endpoint: 'https://fcm.googleapis.com/fcm/send/synthetic',
    toJSON: () => ({ keys: { p256dh: 'public-fixture', auth: 'auth-fixture' } }),
  }
  const subscribe = vi.fn().mockResolvedValue(subscription)
  const register = vi.fn().mockResolvedValue({})
  vi.stubGlobal('isSecureContext', true)
  vi.stubGlobal('Notification', { requestPermission, permission: 'granted' })
  vi.stubGlobal('PushManager', class {})
  vi.stubGlobal('navigator', {
    serviceWorker: { register, getRegistration: async () => ({
      pushManager: { getSubscription: async () => subscription },
    }), ready: Promise.resolve({
      pushManager: { getSubscription: async () => null, subscribe },
    }) },
  })
  vi.mocked(api).mockResolvedValueOnce({ enabled: true, public_key: 'AA' })
  render(<PushSettings />)
  expect(requestPermission).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole('button', { name: 'Enable on this device' }))
  expect(await screen.findByRole('status')).toHaveTextContent('Push enabled on this device')
  expect(requestPermission).toHaveBeenCalledOnce()
  expect(register).toHaveBeenCalledWith('/sw.js')
  expect(subscribe).toHaveBeenCalledOnce()
  expect(api).toHaveBeenCalledWith('push/subscriptions', 'POST', expect.objectContaining({ endpoint: subscription.endpoint }))
  vi.mocked(api).mockResolvedValueOnce({ accepted: true })
  fireEvent.click(screen.getByRole('button', { name: 'Send push test' }))
  expect(await screen.findByRole('status')).toHaveTextContent('Push service accepted the test')
  expect(api).toHaveBeenLastCalledWith('push/test', 'POST', { endpoint: subscription.endpoint })
})
