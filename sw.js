const CACHE_NAME = 'mattang-v1.0.4'; // 캐시 버전 업데이트
const urlsToCache = [
  '/',
  '/static/style.css',
  '/static/main.js',
  '/static/manifest.json',
  '/static/mattang.png'
];

// 서비스 워커 설치
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('Opened cache');
        const urlsWithQuery = urlsToCache.map(url => {
          if (url.startsWith('/static/')) {
            return `${url}?v=${CACHE_NAME}`;
          }
          return url;
        });
        return cache.addAll(urlsWithQuery);
      })
  );
});

// 서비스 워커 활성화
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// 네트워크 요청 가로채기 (네트워크 우선 전략)
self.addEventListener('fetch', function(event) {
  // API 요청은 캐시하지 않음
  if (event.request.url.includes('/search')) {
    event.respondWith(fetch(event.request));
    return;
  }

  event.respondWith(
    fetch(event.request).then(function(response) {
      // 네트워크에서 성공적으로 가져왔을 때
      if (response && response.status === 200 && response.type === 'basic') {
        const responseToCache = response.clone();
        caches.open(CACHE_NAME).then(function(cache) {
          cache.put(event.request, responseToCache);
        });
      }
      return response;
    }).catch(function() {
      // 네트워크 실패 시 캐시에서 찾아서 반환
      return caches.match(event.request);
    })
  );
});

// 백그라운드 동기화 (오프라인 지원)
self.addEventListener('sync', function(event) {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

// 백그라운드 동기화 함수
function doBackgroundSync() {
  return new Promise(function(resolve, reject) {
    // 오프라인에서 저장된 데이터를 온라인에서 동기화
    console.log('Background sync triggered');
    resolve();
  });
}

// 푸시 알림 처리
self.addEventListener('push', function(event) {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body,
      icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" rx="20" fill="%234CAF50"/><text x="50" y="65" font-size="60" text-anchor="middle" fill="white">🍜</text></svg>',
      badge: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" rx="20" fill="%234CAF50"/><text x="50" y="65" font-size="60" text-anchor="middle" fill="white">🍜</text></svg>',
      vibrate: [200, 100, 200],
      data: {
        url: data.url
      }
    };

    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  }
});

// 알림 클릭 처리
self.addEventListener('notificationclick', function(event) {
  event.notification.close();

  if (event.notification.data.url) {
    event.waitUntil(
      clients.openWindow(event.notification.data.url)
    );
  }
});

// 메시지 처리
self.addEventListener('message', function(event) {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
}); 