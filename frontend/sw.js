// Service Worker minimalista (usado para habilitar a instalação PWA via recurso 'Add to Home Screen' dos celulares)
const CACHE_NAME = 'culto-app-v1';

// Evento de instalação do SW
self.addEventListener('install', event => {
  self.skipWaiting();
});

// Evento de ativação do SW
self.addEventListener('activate', event => {
  event.waitUntil(clients.claim());
});

// Evento Fetch (Interceptor Pass-Through -> ou seja, manda ver em rede normalmente. Não afeta carregamento API ao Vivo)
self.addEventListener('fetch', event => {
  event.respondWith(
    fetch(event.request).catch(() => {
      // Se tivermos erro de rede absoluto e não houver cache offline
      return new Response("Sem conexão", { 
        status: 503, 
        statusText: "Site offline, tente mais tarde." 
      });
    })
  );
});
