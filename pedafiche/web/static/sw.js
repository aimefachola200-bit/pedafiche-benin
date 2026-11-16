/* PédaFiche Bénin : application installable (ordinateur, téléphone, tablette).
   Seuls les fichiers de présentation sont gardés : jamais les pages ni les données de l'école. */
const CACHE = 'pedafiche-v2.2.0';
const FICHIERS = ['/static/style.css', '/static/icons/icon-192.png', '/static/icons/icon-512.png', '/static/icons/favicon-32.png'];
self.addEventListener('install', e => e.waitUntil(caches.open(CACHE).then(c => c.addAll(FICHIERS)).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(caches.keys()
  .then(cles => Promise.all(cles.filter(k => k.startsWith('pedafiche-') && k !== CACHE).map(k => caches.delete(k))))
  .then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  const r = e.request;
  if (r.method !== 'GET') return;
  const url = new URL(r.url);
  if (url.origin !== location.origin) return;
  if (FICHIERS.includes(url.pathname)) { e.respondWith(caches.match(r).then(x => x || fetch(r))); return; }
  if (r.mode === 'navigate') {
    e.respondWith(fetch(r).catch(() => new Response(
      '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
      '<title>Hors connexion</title><body style="font:18px sans-serif;padding:2rem;text-align:center">' +
      '<h1>Pas de connexion Internet</h1><p>PédaFiche a besoin d\'Internet pour afficher vos classes. ' +
      'Reconnectez-vous puis actualisez la page.</p></body>',
      { headers: { 'Content-Type': 'text/html; charset=utf-8' } })));
  }
});
