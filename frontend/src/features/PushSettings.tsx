import { useState } from 'react'
import { api, errorText } from './api'
import { disablePush } from './push-client'
export function PushSettings() {
  const [busy, setBusy] = useState(false), [message, setMessage] = useState(''), [error, setError] = useState('')
  async function enable() {
    setBusy(true); setError(''); setMessage('')
    try {
      if (!('serviceWorker' in navigator) || !('PushManager' in window) || !window.isSecureContext) throw new Error('This device needs a compatible browser and HTTPS for push notifications.')
      // Request directly from the click handler, before network work (required by Safari).
      const permission = await Notification.requestPermission()
      if (permission !== 'granted') throw new Error('Notifications were not permitted. You can change this in browser settings.')
      const config = await api<{ enabled: boolean; public_key: string }>('push/configuration')
      if (!config.enabled) throw new Error('Push delivery is not configured yet. In-app reminders remain available.')
      await navigator.serviceWorker.register('/sw.js')
      const registration = await navigator.serviceWorker.ready
      const key = Uint8Array.from(atob(config.public_key.replace(/-/g, '+').replace(/_/g, '/')), c => c.charCodeAt(0))
      const subscription = await registration.pushManager.getSubscription() || await registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: key })
      const data = subscription.toJSON()
      await api('push/subscriptions', 'POST', { endpoint: subscription.endpoint, p256dh: data.keys?.p256dh, auth: data.keys?.auth })
      setMessage('Push enabled on this device. Send a test notification to check delivery.')
    } catch (e) { setError(errorText(e)) } finally { setBusy(false) }
  }
  return <section className="feature-card"><h2>Device notifications</h2><p>On supported iPhones and iPads, add Momentum to your Home Screen and open it there first. Push delivery can be delayed or unavailable. Notifications show generic text to protect your privacy.</p><div className="feature-actions"><button disabled={busy} onClick={() => void enable()}>Enable on this device</button><button disabled={busy} onClick={async () => { setBusy(true); setError(''); try { await disablePush(); setMessage('Push disabled on this device.') } catch (e) { setError(errorText(e)) } finally { setBusy(false) } }}>Disable on this device</button><button disabled={busy} onClick={async () => { setBusy(true); setError(''); try { await api('reminders/test', 'POST'); setMessage('Test queued. Delivery requires the worker and is subject to quiet hours.') } catch (e) { setError(errorText(e)) } finally { setBusy(false) } }}>Send push test</button></div>{message && <p role="status">{message}</p>}{error && <p role="alert" className="notice-error">{error}</p>}</section>
}
