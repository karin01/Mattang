const CACHE_NAME = 'mattang-v1.0.5'; // 캐시 버전 업데이트
const urlsToCache = [
  '/', // index.html
  '/style.css',
  '/main.js',
  '/manifest.json',
  '/mattang.png'
];

// 서비스 워커 설치
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('Opened cache');
        // 버전 쿼리 추가
        const urlsWithQuery = urlsToCache.map(url => `${url}?v=${CACHE_NAME}`);
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
      return caches.match(event.request).then(response => {
        return response || caches.match('/'); // 오프라인일 때 기본 페이지 보여주기
      });
    })
  );
});

// ... (push, notificationclick, message 이벤트 리스너는 기존과 동일) 