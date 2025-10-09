// Service Worker for PWA functionality
const CACHE_NAME = "restaurant-v2.0.0";
const urlsToCache = [
  "/",
  "/static/style.css",
  "/static/main.js",
  "/static/default.png",
  "/static/default.png",
  // Do not pre-cache the /menu HTML page to avoid serving stale personalized content.
  // The menu data is fetched via API or embedded into pages; avoid caching HTML here.
  "/about",
  "/contact",
];

// Install event
self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(urlsToCache).catch(function (err) {
        console.warn("Service worker cache.addAll failed:", err);
        // Optionally, try to add files one by one
        return Promise.all(
          urlsToCache.map((url) =>
            cache.add(url).catch((e) => console.warn("Failed to cache", url, e))
          )
        );
      });
    })
  );
});

// Fetch event
self.addEventListener("fetch", function (event) {
  event.respondWith(
    caches.match(event.request).then(function (response) {
      // Return cached version or fetch from network
      return response || fetch(event.request);
    })
  );
});

// Activate event
self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (cacheNames) {
      return Promise.all(
        cacheNames.map(function (cacheName) {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
