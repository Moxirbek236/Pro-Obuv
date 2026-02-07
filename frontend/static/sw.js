const CACHE_NAME = 'safety-admin-v1';
const urlsToCache = [
    '/super-admin/dashboard',
    '/static/css/admin-panel-responsive.css',
    '/static/img/default.webp'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                if (response) {
                    return response;
                }
                return fetch(event.request);
            })
    );
});
