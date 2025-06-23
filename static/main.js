document.getElementById('query').focus();

let currentLang = 'ko';
let myLat = null, myLng = null;

const langTexts = {
    ko: {
        title: '맛집 통합 검색',
        subtitle: '요즘 핫한 곳, 한 번에 찾기',
        placeholder: '지역, 음식, 키워드로 검색 (예: 성수 파스타)',
        loading: '검색 중...',
        noResult: '검색 결과가 없습니다.<br>다른 키워드로 다시 검색해보세요.',
        error: '검색 중 오류가 발생했습니다.',
        go: '바로가기',
        kakaoAlert: '카카오맵은 정책상 외부에서 바로 접근이 제한될 수 있습니다. 직접 카카오맵에서 검색해 주세요.',
        engBtn: 'Eng',
    },
    en: {
        title: 'Restaurant Search',
        subtitle: 'Find trending places at once',
        placeholder: 'Search by area, food, or keyword (e.g. Seongsu pasta)',
        loading: 'Searching...',
        noResult: 'No results found.<br>Try searching with different keywords.',
        error: 'An error occurred during search.',
        go: 'Go',
        kakaoAlert: 'Due to KakaoMap policy, direct access may be restricted. Please search directly on KakaoMap.',
        engBtn: '한글',
    }
};

function updateLangUI() {
    const titleEl = document.querySelector('.mz-title');
    if (titleEl) titleEl.textContent = langTexts[currentLang].title;
    const subtitleEl = document.querySelector('.mz-subtitle');
    if (subtitleEl) subtitleEl.textContent = langTexts[currentLang].subtitle;
    const queryEl = document.getElementById('query');
    if (queryEl) queryEl.placeholder = langTexts[currentLang].placeholder;
    const korToggle = document.getElementById('kor-toggle');
    if (korToggle) korToggle.classList.toggle('active', currentLang === 'ko');
    const engToggle = document.getElementById('eng-toggle');
    if (engToggle) engToggle.classList.toggle('active', currentLang === 'en');
    const loadingP = document.querySelector('.mz-loading p');
    if (loadingP) loadingP.textContent = langTexts[currentLang].loading;
}

function getPlatformBadge(platform) {
    if (platform.includes('카카오')) return '<span class="badge-platform badge-kakao">카카오</span>';
    if (platform.includes('네이버')) return '<span class="badge-platform badge-naver">네이버</span>';
    if (platform.includes('구글')) return '<span class="badge-platform badge-google">구글</span>';
    return `<span class="badge-platform">${platform}</span>`;
}
function getRatingClass(rating) {
    const num = parseFloat(rating);
    if (isNaN(num) || rating === '-') return '';
    if (num >= 4.0) return 'rating-high';
    if (num >= 3.0) return 'rating-mid';
    return 'rating-low';
}

// 내 위치 받아오기 및 거리 계산 추가
if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(function(pos) {
        myLat = pos.coords.latitude;
        myLng = pos.coords.longitude;
    });
}
// 거리 계산 함수
function getDistanceFromLatLonInKm(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2-lat1) * Math.PI/180;
    const dLon = (lon2-lon1) * Math.PI/180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) + Math.cos(lat1 * Math.PI/180) * Math.cos(lat2 * Math.PI/180) * Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

let searchTimeout = null;

function showLongSearchMessage() {
    let msg = document.getElementById('long-search-msg');
    if (!msg) {
        msg = document.createElement('div');
        msg.id = 'long-search-msg';
        msg.style.textAlign = 'center';
        msg.style.marginTop = '1rem';
        msg.style.color = '#888';
        msg.textContent = '흩어져 있는 것을 줍고 있습니다. 잠시만 기다려 주세요.';
        document.querySelector('.mz-loading').appendChild(msg);
    }
}
function hideLongSearchMessage() {
    const msg = document.getElementById('long-search-msg');
    if (msg) msg.remove();
}

let apiBaseUrl = '';

document.addEventListener('DOMContentLoaded', function() {
    // 언어 버튼 바인딩
    const korBtn = document.getElementById('korBtn');
    const engBtn = document.getElementById('engBtn');
    if (korBtn) {
        korBtn.addEventListener('click', () => {
            if (currentLang !== 'ko') {
                currentLang = 'ko';
                updateLangUI();
                document.getElementById('mz-results').innerHTML = '';
            }
        });
    }
    if (engBtn) {
        engBtn.addEventListener('click', () => {
            if (currentLang !== 'en') {
                currentLang = 'en';
                updateLangUI();
                document.getElementById('mz-results').innerHTML = '';
            }
        });
    }
    // 폼 바인딩
    const form = document.getElementById('searchForm');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const query = document.getElementById('query') ? document.getElementById('query').value : document.getElementById('searchInput').value;
            const loading = document.querySelector('.mz-loading');
            const results = document.getElementById('mz-results') || document.getElementById('cardList');
            loading.style.display = 'flex';
            // 로딩 텍스트 변경
            const loadingP = loading.querySelector('p');
            if (loadingP) loadingP.textContent = langTexts[currentLang].loading;
            if (results) results.innerHTML = '';
            hideLongSearchMessage();
            if (searchTimeout) clearTimeout(searchTimeout);
            searchTimeout = setTimeout(showLongSearchMessage, 5000);
            try {
                const response = await fetch(`${apiBaseUrl}/search`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query: query, lang: currentLang })
                });
                const data = await response.json();
                if (searchTimeout) clearTimeout(searchTimeout);
                hideLongSearchMessage();
                if (data.success && data.restaurants.length > 0) {
                    let html = '';
                    data.restaurants.forEach((r, index) => {
                        try {
                            console.log(`[DEBUG] Processing item #${index}`, r);
                            if (myLat && myLng && r.lat && r.lng) {
                                r.distance = getDistanceFromLatLonInKm(myLat, myLng, r.lat, r.lng);
                            }
                            let photo = r.photo ? `<img class='mz-photo' src='${r.photo}' alt='${r.name}' onerror="this.style.display='none';">` : '';
                            
                            let badges = '';
                            const platforms = Array.isArray(r.platform) ? r.platform : [r.platform];
                            badges = platforms.map(p => {
                                const platformName = (p || '').replace('카카오맵','카카오').replace('네이버블로그','네이버').replace('네이버 지도','네이버');
                                let badgeClass = 'badge-default';
                                if (platformName.includes('카카오')) badgeClass = 'badge-kakao';
                                else if (platformName.includes('네이버')) badgeClass = 'badge-naver';
                                else if (platformName.includes('구글')) badgeClass = 'badge-google';
                                return `<span class='mz-badge ${badgeClass}'>${platformName}</span>`;
                            }).join(' ');

                            let rating = r.rating && r.rating !== '-' ? `<span class='mz-rating'>⭐ ${r.rating}</span>` : '';
                            let review = r.review && r.review !== '-' ? `<span class='mz-review'>💬 ${r.review}</span>` : '';
                            let hours = r.hours ? `<span class='mz-hours'>⏰ ${r.hours}</span>` : '';
                            function getKorean(str) {
                                const m = str && str.match(/[가-힣0-9\s()-]+/g);
                                if (!m || !m.join('').replace(/[^가-힣]/g, '').trim()) return str;
                                return m.join('').trim();
                            }
                            
                            let addrText = '';
                            if (r.addr) {
                                if (platforms.some(p => (p || '').toLowerCase().includes('google'))) {
                                    addrText = getKorean(r.addr);
                                } else {
                                    addrText = r.addr;
                                }
                            }

                            let addr = '';
                            if (addrText) {
                                addr = `<div class='mz-addr'>📍 <a href="https://map.naver.com/p/search/${encodeURIComponent(addrText)}" target="_blank" style="text-decoration: none; color: inherit;">${addrText}</a>
                                    <button class="copy-btn" data-addr="${addrText}" title="주소 복사" style="border:none;background:transparent;cursor:pointer;margin-left:4px;font-size:16px;vertical-align:middle;">📋</button>
                                </div>`;
                            }

                            let nameText = '';
                            if (r.name) {
                                if (platforms.some(p => (p || '').toLowerCase().includes('blog'))) {
                                    nameText = r.name;
                                } else {
                                    nameText = getKorean(r.name);
                                }
                            }
                            let name = `<div class="mz-card-title">${nameText}</div>`;
                            
                            let distance = '';
                            if (typeof r.distance === 'number') {
                                if (r.distance < 1) {
                                    distance = `<div class='mz-distance'>내 위치로부터 ${(r.distance*1000).toFixed(0)}m</div>`;
                                } else {
                                    distance = `<div class='mz-distance'>내 위치로부터 ${r.distance.toFixed(2)}km</div>`;
                                }
                            }
                            let link = '';
                            if (platforms.some(p => (p || '').includes('카카오'))) {
                                link = `<a href="#" class="mz-link" onclick="alert('${langTexts[currentLang].kakaoAlert}'); return false;">${langTexts[currentLang].go}</a>`;
                            } else {
                                link = `<a href="${r.link}" class="mz-link" target="_blank">${langTexts[currentLang].go}</a>`;
                            }
                            html += `
                            <div class="mz-card">
                                ${photo}
                                <div class="mz-badges">${badges}</div>
                                ${name}
                                <div class="mz-info-row">${rating}${review}</div>
                                ${addr}
                                ${distance}
                                ${hours}
                                ${link}
                            </div>
                            `;
                        } catch (e) {
                            console.error(`[DEBUG] Error processing item #${index}`, r);
                            console.error(e);
                        }
                    });
                    results.innerHTML = html;
                } else {
                    results.innerHTML = `<div class='alert-message'>${langTexts[currentLang].noResult}</div>`;
                }
            } catch (error) {
                if (searchTimeout) clearTimeout(searchTimeout);
                hideLongSearchMessage();
                results.innerHTML = `<div class='alert-message'>${langTexts[currentLang].error}</div>`;
            } finally {
                loading.style.display = 'none';
            }
        });
    }
    updateLangUI();
});

// 전역 변수
let userLocation = null;
let searchResults = [];

// DOM 요소들
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const loadingContainer = document.getElementById('loadingContainer');
const resultsContainer = document.getElementById('resultsContainer');
const cardList = document.getElementById('cardList');
const locationStatus = document.getElementById('locationStatus');

// 초기화
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
});

// 앱 초기화
async function initializeApp() {
    try {
        await getUserLocation();
    } catch (error) {
        console.error('위치 정보를 가져올 수 없습니다:', error);
        if (locationStatus) locationStatus.textContent = '위치 정보를 사용할 수 없습니다';
    }
}

// 이벤트 리스너 설정
function setupEventListeners() {
    if (searchBtn) searchBtn.addEventListener('click', performSearch);
    if (searchInput) searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
}

// 사용자 위치 가져오기
async function getUserLocation() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            if (locationStatus) locationStatus.textContent = '이 브라우저는 위치 정보를 지원하지 않습니다';
            reject(new Error('Geolocation not supported'));
            return;
        }

        if (locationStatus) locationStatus.textContent = '위치 정보를 가져오는 중...';

        navigator.geolocation.getCurrentPosition(
            (position) => {
                userLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                if (locationStatus) locationStatus.textContent = '위치 정보 준비 완료';
                resolve(userLocation);
            },
            (error) => {
                console.error('위치 정보 오류:', error);
                if (locationStatus) {
                    switch (error.code) {
                        case error.PERMISSION_DENIED:
                            locationStatus.textContent = '위치 정보 접근이 거부되었습니다';
                            break;
                        case error.POSITION_UNAVAILABLE:
                            locationStatus.textContent = '위치 정보를 사용할 수 없습니다';
                            break;
                        case error.TIMEOUT:
                            locationStatus.textContent = '위치 정보 요청 시간이 초과되었습니다';
                            break;
                        default:
                            locationStatus.textContent = '위치 정보를 가져올 수 없습니다';
                    }
                }
                reject(error);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000
            }
        );
    });
}

// 검색 수행
async function performSearch() {
    const query = searchInput.value.trim();
    
    // 안내 메시지 요소 생성 또는 선택
    let notice = document.getElementById('search-notice');
    if (!notice) {
        notice = document.createElement('div');
        notice.id = 'search-notice';
        notice.style.color = '#e53e3e';
        notice.style.marginTop = '8px';
        notice.style.fontSize = '0.95rem';
        notice.style.textAlign = 'center';
        searchInput.parentNode.appendChild(notice);
    }

    if (!query) {
        notice.textContent = '검색어를 입력해주세요.';
        searchInput.focus();
        return;
    } else {
        notice.textContent = '';
    }

    showLoading();
    
    try {
        const results = await searchRestaurants(query);
        displayResults(results);
    } catch (error) {
        console.error('검색 오류:', error);
        showError('검색 중 오류가 발생했습니다. 다시 시도해주세요.');
    } finally {
        hideLoading();
    }
}

// 맛집 검색 API 호출
async function searchRestaurants(query) {
    const response = await fetch(`${apiBaseUrl}/search`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query })
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.results || [];
}

// 결과 표시
function displayResults(results) {
    searchResults = results;
    
    if (results.length === 0) {
        cardList.innerHTML = `
            <div class="no-results">
                <h3>검색 결과가 없습니다</h3>
                <p>다른 검색어로 다시 시도해보세요.</p>
            </div>
        `;
        return;
    }

    const cardsHTML = results.map(restaurant => createRestaurantCard(restaurant)).join('');
    cardList.innerHTML = cardsHTML;
}

// 맛집 카드 생성
function createRestaurantCard(restaurant) {
    const distance = userLocation ? calculateDistance(userLocation, restaurant) : null;
    const distanceText = distance ? `${distance.toFixed(1)}km` : '';
    
    return `
        <div class="card">
            <div class="card-header">
                <span class="platform-badge ${getPlatformClass(restaurant.platform)}">
                    ${restaurant.platform}
                </span>
                <h3 class="restaurant-name">${escapeHtml(restaurant.name)}</h3>
                <div class="restaurant-info">
                    ${restaurant.rating && restaurant.rating !== '-' ? 
                        `<span class="info-item rating">⭐ ${restaurant.rating}</span>` : ''}
                    ${restaurant.review && restaurant.review !== '-' ? 
                        `<span class="info-item review">💬 ${restaurant.review}</span>` : ''}
                </div>
            </div>
            <div class="card-body">
                ${restaurant.addr ? `<div class="address">📍 ${escapeHtml(restaurant.addr)}</div>` : ''}
                ${distanceText ? `<div class="distance">🚶‍♂️ 현재 위치에서 ${distanceText}</div>` : ''}
                ${restaurant.hours && restaurant.hours !== '-' ? 
                    `<div class="hours">🕒 ${escapeHtml(restaurant.hours)}</div>` : ''}
            </div>
            <div class="card-footer">
                <a href="${restaurant.link}" target="_blank" class="go-button">
                    ${getPlatformButtonText(restaurant.platform)}
                </a>
            </div>
        </div>
    `;
}

// 플랫폼별 CSS 클래스 반환
function getPlatformClass(platform) {
    const platformMap = {
        '카카오맵': 'kakao',
        '구글맵': 'google',
        '네이버블로그': 'naver',
        '망고플레이트': 'mangoplate'
    };
    return platformMap[platform] || 'default';
}

// 플랫폼별 버튼 텍스트 반환
function getPlatformButtonText(platform) {
    const buttonTextMap = {
        '카카오맵': '카카오맵에서 보기',
        '구글맵': '구글맵에서 보기',
        '네이버블로그': '네이버블로그 보기',
        '망고플레이트': '망고플레이트에서 보기'
    };
    return buttonTextMap[platform] || '자세히 보기';
}

// 거리 계산 (Haversine 공식)
function calculateDistance(userLoc, restaurant) {
    if (!restaurant.lat || !restaurant.lng) {
        return null;
    }

    const R = 6371; // 지구의 반지름 (km)
    const dLat = (restaurant.lat - userLoc.lat) * Math.PI / 180;
    const dLng = (restaurant.lng - userLoc.lng) * Math.PI / 180;
    
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(userLoc.lat * Math.PI / 180) * Math.cos(restaurant.lat * Math.PI / 180) *
              Math.sin(dLng/2) * Math.sin(dLng/2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    const distance = R * c;
    
    return distance;
}

// HTML 이스케이프
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 로딩 표시
function showLoading() {
    loadingContainer.style.display = 'flex';
    resultsContainer.style.display = 'none';
}

// 로딩 숨기기
function hideLoading() {
    loadingContainer.style.display = 'none';
    resultsContainer.style.display = 'block';
}

// 오류 표시
function showError(message) {
    cardList.innerHTML = `
        <div class="error-message">
            <h3>오류가 발생했습니다</h3>
            <p>${message}</p>
        </div>
    `;
    hideLoading();
}

// 네트워크 상태 확인
function checkNetworkStatus() {
    if (!navigator.onLine) {
        showError('인터넷 연결을 확인해주세요.');
    }
}

// 오프라인/온라인 이벤트 리스너
window.addEventListener('online', function() {
    locationStatus.textContent = '위치 정보 준비 완료';
});

window.addEventListener('offline', function() {
    locationStatus.textContent = '오프라인 모드';
});

// 앱 설치 프롬프트 (PWA 지원)
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    
    // 설치 버튼 표시 로직을 여기에 추가할 수 있습니다
    console.log('앱 설치 가능');
});

// 앱 설치 완료 이벤트
window.addEventListener('appinstalled', (evt) => {
    console.log('앱이 성공적으로 설치되었습니다');
});

// 터치 이벤트 최적화 (모바일)
function addTouchOptimization() {
    // 터치 이벤트에 대한 지연 시간 최소화
    document.addEventListener('touchstart', function() {}, {passive: true});
    document.addEventListener('touchmove', function() {}, {passive: true});
    document.addEventListener('touchend', function() {}, {passive: true});
}

// 앱 초기화 시 터치 최적화 적용
addTouchOptimization();

// PWA 서비스 워커 등록
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js', { scope: '/' }) // 경로 수정
            .then(function(registration) {
                console.log('SW registered: ', registration);
            })
            .catch(function(error) {
                console.error('SW registration failed: ', error);
            });
    });
}

// 복사 버튼 기능 추가 (파일 하단에 삽입)
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('copy-btn')) {
        const btn = e.target;
        const addr = btn.getAttribute('data-addr');
        if (navigator.clipboard) {
            navigator.clipboard.writeText(addr).then(() => {
                const prevTitle = btn.title;
                btn.title = '복사됨!';
                setTimeout(() => { btn.title = prevTitle; }, 1000);
            });
        } else {
            // fallback for old browsers
            const textarea = document.createElement('textarea');
            textarea.value = addr;
            document.body.appendChild(textarea);
            textarea.select();
            try {
                document.execCommand('copy');
                const prevTitle = btn.title;
                btn.title = '복사됨!';
                setTimeout(() => { btn.title = prevTitle; }, 1000);
            } catch (err) {}
            document.body.removeChild(textarea);
        }
    }
}); 