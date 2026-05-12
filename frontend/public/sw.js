/**
 * Minimal service worker — enables PWA install on iOS Safari + Android.
 * Intentionally no caching (would interfere with the real-time WebSocket app).
 */
self.addEventListener('install', (event) => {
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim())
})

self.addEventListener('fetch', (event) => {
  // Pass through. Don't cache — JARVIS is online-only and stateful.
})
