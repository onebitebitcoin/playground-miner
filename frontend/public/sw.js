const CACHE_NAME = 'bitcoin-playground-v2';
// Cache only stable, guaranteed assets. Vite outputs hashed assets under /assets,
// which change per build; caching them here would cause 404 on install.
const urlsToCache = [
  '/',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version if available
        if (response) {
          return response;
        }

        // Try to fetch from network with error handling
        return fetch(event.request)
          .catch((error) => {
            console.warn('Service Worker: Fetch failed for', event.request.url, error);

            // For navigation requests, return the cached index.html as fallback
            if (event.request.mode === 'navigate') {
              return caches.match('/');
            }

            // For other requests, just let them fail gracefully
            throw error;
          });
      })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
