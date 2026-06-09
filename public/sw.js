/**
 * SLH Spark Service Worker v1.0
 * Strategy: network-first for HTML (fresh content), cache-first for static assets.
 * API calls NEVER cached.
 *
 * Cache invalidation: bump CACHE_VERSION on breaking changes.
 * Updated: 2026-04-18
 */

const CACHE_VERSION = 'slh-v1.0-20260418';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const PAGES_CACHE = `${CACHE_VERSION}-pages`;

const CRITICAL_ASSETS = [
  '/',
  '/index.html',
  '/css/slh-design-system.css',
  '/css/shared.css?v=20260417',
  '/js/shared.js',
  '/js/slh-flip.js?v=20260417',
  '/js/translations.js',
  '/favicon-32.png',
  '/icon-192.png',
  '/icon-512.png',
  '/manifest.json',
];

// Install — precache critical assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => Promise.allSettled(
        CRITICAL_ASSETS.map(url => cache.add(new Request(url, { cache: 'reload' })))
      ))
      .then(() => self.skipWaiting())
      .catch(err => console.warn('[SW] Precache partial:', err))
  );
});

// Activate — clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(names =>
      Promise.all(
        names.filter(n => !n.startsWith(CACHE_VERSION)).map(n => caches.delete(n))
      )
    ).then(() => self.clients.claim())
  );
});

// Fetch — route by type
self.addEventListener('fetch', event => {
  const { request } = event;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);

  // Never cache cross-origin or API calls
  if (url.hostname !== self.location.hostname) return;
  if (url.pathname.startsWith('/api/')) return;

  // Static assets: cache-first
  if (/\.(css|js|png|jpg|jpeg|webp|svg|woff2?|ttf|ico|json)(\?.*)?$/.test(url.pathname)) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // HTML pages: network-first with fallback
  if (request.destination === 'document' || url.pathname.endsWith('.html') || url.pathname === '/') {
    event.respondWith(networkFirst(request));
    return;
  }
});

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone()).catch(() => {});
    }
    return response;
  } catch (e) {
    return new Response('offline', { status: 503 });
  }
}

async function networkFirst(request) {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    const response = await fetch(request, { signal: controller.signal });
    clearTimeout(timeout);
    if (response.ok) {
      const cache = await caches.open(PAGES_CACHE);
      cache.put(request, response.clone()).catch(() => {});
    }
    return response;
  } catch (e) {
    const cached = await caches.match(request);
    if (cached) return cached;
    return new Response(
      `<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8"><title>Offline · SLH Spark</title></head>
       <body style="font-family:system-ui;background:#05080f;color:#f5f5f8;text-align:center;padding:80px 20px">
       <h1 style="color:#00ff41">💡 אתה offline</h1>
       <p>אין חיבור לאינטרנט. נסה שוב כשיחזור.</p>
       <p><a href="/" style="color:#00e5ff">→ רענן</a></p>
       </body></html>`,
      { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } }
    );
  }
}

// Listen for messages from page (e.g., "clear cache")
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    caches.keys().then(keys => Promise.all(keys.map(k => caches.delete(k))));
  }
});
