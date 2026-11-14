import { api } from './api'
export async function disablePush() {
  if (!('serviceWorker' in navigator)) return
  const registration = await navigator.serviceWorker.getRegistration('/')
  const subscription = await registration?.pushManager.getSubscription()
  if (subscription) {
    await api('push/subscriptions', 'DELETE', { endpoint: subscription.endpoint })
    await subscription.unsubscribe()
  }
}
