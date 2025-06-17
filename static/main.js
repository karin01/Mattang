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
    document.querySelector('.mz-title').textContent = langTexts[currentLang].title;
    document.querySelector('.mz-subtitle').textContent = langTexts[currentLang].subtitle;
    document.getElementById('query').placeholder = langTexts[currentLang].placeholder;
    // Highlight active lang button
    document.getElementById('kor-toggle').classList.toggle('active', currentLang === 'ko');
    document.getElementById('eng-toggle').classList.toggle('active', currentLang === 'en');
    // If loading is visible, update its text
    const loadingP = document.querySelector('.mz-loading p');
    if (loadingP) loadingP.textContent = langTexts[currentLang].loading;
}

document.getElementById('kor-toggle').addEventListener('click', () => {
    if (currentLang !== 'ko') {
        currentLang = 'ko';
        updateLangUI();
        document.getElementById('mz-results').innerHTML = '';
    }
});
document.getElementById('eng-toggle').addEventListener('click', () => {
    if (currentLang !== 'en') {
        currentLang = 'en';
        updateLangUI();
        document.getElementById('mz-results').innerHTML = '';
    }
});

updateLangUI();

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
        msg.textContent = '검색이 오래 걸릴 수 있습니다. 잠시만 기다려 주세요.';
        document.querySelector('.mz-loading').appendChild(msg);
    }
}
function hideLongSearchMessage() {
    const msg = document.getElementById('long-search-msg');
    if (msg) msg.remove();
}

document.getElementById('searchForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = document.getElementById('query').value;
    const loading = document.querySelector('.mz-loading');
    const results = document.getElementById('mz-results');
    loading.style.display = 'flex';
    document.querySelector('.mz-loading p').textContent = langTexts[currentLang].loading;
    results.innerHTML = '';
    hideLongSearchMessage();
    if (searchTimeout) clearTimeout(searchTimeout);
    searchTimeout = setTimeout(showLongSearchMessage, 5000);
    try {
        const response = await fetch('https://mattang-server-595332420442.asia-northeast3.run.app/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `query=${encodeURIComponent(query)}&lang=${currentLang}`
        });
        const data = await response.json();
        if (searchTimeout) clearTimeout(searchTimeout);
        hideLongSearchMessage();
        if (data.success && data.restaurants.length > 0) {
            let html = '';
            data.restaurants.forEach(r => {
                // 인스타그램 카드 제외
                if (r.platform && (r.platform.includes('인스타그램') || r.platform.toLowerCase().includes('instagram'))) return;
                // 내 위치와 맛집 위치가 모두 있으면 거리 계산
                if (myLat && myLng && r.lat && r.lng) {
                    r.distance = getDistanceFromLatLonInKm(myLat, myLng, r.lat, r.lng);
                }
                let photo = r.photo ? `<img class='mz-photo' src='${r.photo}' alt='${r.name}'>` : '';
                let badge = `<span class='mz-badge'>${r.platform.replace('카카오맵','카카오').replace('네이버블로그','네이버블로그').replace('네이버 블로그','네이버블로그').replace('네이버','네이버').replace('구글','구글')}</span>`;
                let rating = r.rating && r.rating !== '-' ? `<span class='mz-rating'><i class=\"fas fa-star\"></i> ${r.rating}</span>` : '';
                let review = r.review && r.review !== '-' ? `<span class='mz-review'><i class=\"fas fa-comment-dots\"></i> ${r.review}</span>` : '';
                let hours = r.hours ? `<span class='mz-hours'><i class=\"fas fa-clock mz-info-icon\"></i> ${r.hours}</span>` : '';
                function getKorean(str) {
                    const m = str && str.match(/[가-힣0-9\s\-()]+/g);
                    if (!m || !m.join('').replace(/[^가-힣]/g, '').trim()) return str;
                    return m.join('').trim();
                }
                let addr = '';
                let name = '';
                if (r.platform && (r.platform.includes('구글') || r.platform.toLowerCase().includes('google'))) {
                    addr = r.addr ? `<div class='mz-addr'><i class=\"fas fa-map-marker-alt mz-info-icon\"></i> ${getKorean(r.addr)}</div>` : '';
                    name = `<div class=\"mz-card-title\">${getKorean(r.name)}</div>`;
                } else if (r.platform && (r.platform.includes('네이버블로그') || r.platform.includes('네이버 블로그') || r.platform.toLowerCase().includes('blog'))) {
                    addr = r.addr ? `<div class='mz-addr'><i class=\"fas fa-map-marker-alt mz-info-icon\"></i> ${r.addr}</div>` : '';
                    name = `<div class=\"mz-card-title\">${r.name}</div>`;
                } else {
                    addr = r.addr ? `<div class='mz-addr'><i class=\"fas fa-map-marker-alt mz-info-icon\"></i> ${r.addr}</div>` : '';
                    name = `<div class=\"mz-card-title\">${getKorean(r.name)}</div>`;
                }
                let distance = '';
                if (typeof r.distance === 'number') {
                    if (r.distance < 1) {
                        distance = `<div class='mz-distance'>내 위치로부터 ${(r.distance*1000).toFixed(0)}m</div>`;
                    } else {
                        distance = `<div class='mz-distance'>내 위치로부터 ${r.distance.toFixed(2)}km</div>`;
                    }
                }
                let link = '';
                if (r.platform && r.platform.includes('카카오')) {
                    link = `<a href=\"#\" class=\"mz-link\" onclick=\"alert('${langTexts[currentLang].kakaoAlert}'); return false;\"><i class=\"fas fa-external-link-alt\"></i> ${langTexts[currentLang].go}</a>`;
                } else {
                    link = `<a href=\"${r.link}\" class=\"mz-link\" target=\"_blank\"><i class=\"fas fa-external-link-alt\"></i> ${langTexts[currentLang].go}</a>`;
                }
                html += `
                <div class=\"mz-card\">
                    ${photo}
                    ${badge}
                    ${name}
                    <div class=\"mz-info-row\">${rating}${review}</div>
                    ${addr}
                    ${distance}
                    ${hours}
                    ${link}
                </div>
                `;
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