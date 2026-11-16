/* silence. — Cache hors connexion, version 3.15.5 */
'use strict';
const CACHE = 'silence-v3.15.5';
const ASSETS = ['./', './index.html', './styles.css?v=3.15.5', './app.js?v=3.15.5', './manifest.webmanifest?v=3.15.5', './icons/icon-192.png?v=3.15.5', './icons/icon-512.png?v=3.15.5', './icons/icon-180.png?v=3.15.5', './icons/favicon-32.png?v=3.15.5', './icons/favicon-48.png?v=3.15.5', './favicon.ico?v=3.15.5', './og-image.jpg', './sounds/goutte.wav'];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)));
  self.skipWaiting();
});
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(key => key.startsWith('silence-') && key !== CACHE).map(key => caches.delete(key)));
    await self.clients.claim();
  })());
});
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const req = event.request;
  const url = new URL(req.url);
  const scope = new URL(self.registration.scope);
  if (url.origin !== scope.origin || !url.pathname.startsWith(scope.pathname)) return;
  // Les assets versionnés sont cohérents et servis depuis le cache installé atomiquement.
  if (url.pathname.endsWith('/app.js') || url.pathname.endsWith('/styles.css') || url.pathname.includes('/icons/')) {
    event.respondWith(caches.match(req).then(hit => hit || fetch(req)));
    return;
  }
  // La navigation récupère la dernière version en ligne, avec repli hors connexion.
  if (req.mode === 'navigate') {
    event.respondWith(fetch(req).then(response => {
      if (response.ok) {
        const copy = response.clone();
        void caches.open(CACHE).then(cache => cache.put('./index.html', copy));
      }
      return response;
    }).catch(() => caches.match('./index.html')));
    return;
  }
  event.respondWith(caches.match(req).then(hit => hit || fetch(req)));
});
