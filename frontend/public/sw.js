// Service Worker DISABLED - Immediately unregister and clean up
console.log('Service Worker: Disabling and cleaning up...');

self.addEventListener('install', (event) => {
  // Skip waiting and take control immediately
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    // Clear all caches
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          console.log('Deleting cache:', cacheName);
          return caches.delete(cacheName);
        })
      );
    }).then(() => {
      // Unregister this service worker
      console.log('Service Worker: Unregistering...');
      return self.registration.unregister();
    }).then(() => {
      // Take control of all clients
      return self.clients.claim();
    })
  );
});

// Do not handle any fetch events
self.addEventListener('fetch', (event) => {
  // Let all requests go through normally to the network
  return;
});
