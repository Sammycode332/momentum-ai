// No API, authentication or workspace caching: private records stay out of CacheStorage.
self.addEventListener('push', event => {
  let tag = 'momentum-reminder'
  try { tag = event.data?.json().tag || tag } catch { /* Generic notification on malformed payload. */ }
  event.waitUntil(self.registration.showNotification('Momentum AI', {
    body: 'You have a reminder. Open your workspace to view it.',
    tag, icon: '/icon.svg', data: { url: '/?view=notifications' },
  }))
})
self.addEventListener('notificationclick', event => {
  event.notification.close()
  event.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(async clients => {
    const client = clients.find(item => new URL(item.url).origin === self.location.origin)
    if (client) { await client.navigate('/?view=notifications'); return client.focus() }
    return self.clients.openWindow('/?view=notifications')
  }))
})
