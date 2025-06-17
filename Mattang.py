import subprocess
import sys
import time
import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify
import re
import os
from selenium.webdriver.common.keys import Keys
import requests
import threading
import webbrowser
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import json
import logging
from datetime import datetime

# 패키지 자동 설치
def install_packages():
    packages = ['requests', 'beautifulsoup4', 'selenium', 'flask', 'webdriver_manager']
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_packages()

# 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
app = Flask(__name__, template_folder=TEMPLATE_DIR)

# templates 디렉토리 생성
if not os.path.exists(TEMPLATE_DIR):
    os.makedirs(TEMPLATE_DIR)

# SQLite 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect(os.path.join(BASE_DIR, 'restaurants.db'))  # 파일 기반 DB 사용
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS restaurants
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT, url TEXT, content TEXT, category TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    return conn

# 카테고리 분류 함수 (사용하지 않지만 남겨둠)
def classify_category(content):
    content = content.lower()
    categories = {
        '한식': ['한식', '김치', '비빔밥', '불고기', '삼겹살', '치킨', '떡볶이', '순대', '족발', '보쌈'],
        '중식': ['중식', '짜장면', '탕수육', '마라샹궈', '훠궈', '깐풍기', '깐풍기', '마파두부'],
        '일식': ['일식', '초밥', '라멘', '우동', '돈부리', '규동', '스키야키', '오니기리'],
        '양식': ['양식', '파스타', '피자', '스테이크', '햄버거', '샐러드', '샌드위치'],
        '카페': ['카페', '커피', '디저트', '케이크', '마카롱', '아이스크림', '빙수']
    }
    for category, keywords in categories.items():
        if any(keyword in content for keyword in keywords):
            return category
    return '기타'

# 네이버 지도 크롤링 함수
def crawl_naver_map(query, max_places=10):
    print("[DEBUG][NaverMap] 함수 진입")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    results = []
    try:
        url = f"https://map.naver.com/p/search/{query}"
        print("[DEBUG][NaverMap] URL:", url)
        driver.get(url)
        time.sleep(3)
        try:
            driver.switch_to.frame('searchIframe')
            print("[DEBUG][NaverMap] searchIframe 진입 성공")
        except Exception as e:
            print("[DEBUG][NaverMap] searchIframe 진입 실패:", e)
            driver.quit()
            return results
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        items = soup.select('li.VLTHu')
        print("[DEBUG][NaverMap] items 개수:", len(items))
        for item in items[:max_places]:
            try:
                name = item.select_one('span.place_bluelink').text.strip()
                rating = item.select_one('span.PXMot').text.strip() if item.select_one('span.PXMot') else '-'
                review = item.select_one('span.YDIN4').text.strip() if item.select_one('span.YDIN4') else '-'
                addr = item.select_one('span.LDgIH').text.strip() if item.select_one('span.LDgIH') else '-'
                # 네이버 장소 ID 추출 및 상세페이지 링크 생성
                a_tag = item.select_one('a')
                link = ''
                if a_tag and 'href' in a_tag.attrs:
                    href = a_tag['href']
                    # /p/entry/place/장소ID 형태에서 장소ID만 추출
                    m = re.search(r'/place/(\d+)', href)
                    if m:
                        place_id = m.group(1)
                        link = f'https://place.map.naver.com/{place_id}'
                    else:
                        link = 'https://map.naver.com' + href
                results.append({
                    'platform': '네이버지도',
                    'name': name,
                    'rating': rating,
                    'review': review,
                    'addr': addr,
                    'link': link
                })
            except Exception as e:
                print('[DEBUG][NaverMap] Error:', e)
                continue
    except Exception as e:
        print('[DEBUG][NaverMap] Main Error:', e)
    finally:
        driver.quit()
    return results

# 카카오맵 크롤링 함수
def crawl_kakao_map(query, max_places=10):
    print("[DEBUG][KakaoMap] 함수 진입")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    results = []
    try:
        url = f"https://map.kakao.com/"
        print("[DEBUG][KakaoMap] URL:", url)
        driver.get(url)
        time.sleep(2)
        try:
            search_box = driver.find_element(By.ID, 'search.keyword.query')
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            print("[DEBUG][KakaoMap] 검색어 입력 및 검색 실행")
        except Exception as e:
            print("[DEBUG][KakaoMap] 검색창 진입 실패:", e)
            driver.quit()
            return results
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        items = soup.select('li.PlaceItem')
        print("[DEBUG][KakaoMap] items 개수:", len(items))
        for item in items[:max_places]:
            try:
                name = item.select_one('a.link_name').text.strip()
                rating = item.select_one('em.num').text.strip() if item.select_one('em.num') else '-'
                review_text = item.select_one('span.review').text.strip() if item.select_one('span.review') else '-'
                review = re.sub(r'[^0-9]', '', review_text) if review_text != '-' else '-'
                addr = item.select_one('div.addr').text.strip() if item.select_one('div.addr') else '-'
                # 장소 ID 추출 및 링크 생성
                place_id = item.get('data-id') or item.get('data-place-id')
                link = f'https://place.map.kakao.com/{place_id}#comment' if place_id else ''
                # 위도/경도 추출
                lat = item.get('data-y')
                lng = item.get('data-x')
                if (not lat or not lng) and addr and addr != '-':
                    lat, lng = geocode_kakao(addr)
                # 카카오맵 영업시간
                hours_elem = item.select_one('div.openHour, span.openHour')
                hours = hours_elem.text.strip() if hours_elem else '-'
                # 카카오맵 썸네일 이미지 추출
                img_tag = item.select_one('img.thumb_img') or item.select_one('div.thumb img')
                img_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else None
                results.append({
                    'platform': '카카오맵',
                    'name': name,
                    'rating': rating,
                    'review': review,
                    'addr': addr,
                    'hours': hours,
                    'link': link,
                    'photo': img_url,
                    'lat': lat,
                    'lng': lng
                })
            except Exception as e:
                print('[DEBUG][KakaoMap] Error:', e)
                continue
    except Exception as e:
        print('[DEBUG][KakaoMap] Main Error:', e)
    finally:
        driver.quit()
    return results

# 구글 지도 크롤링 함수
GOOGLE_API_KEY = 'AIzaSyCeLfdnl1LWzVOopu6Ab_sJYtr1bi-OKjk'

def get_place_id(query, api_key):
    url = f'https://maps.googleapis.com/maps/api/place/textsearch/json'
    params = {
        'query': query,
        'key': api_key,
        'language': 'en'
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    if data['status'] == 'OK' and data['results']:
        return data['results'][0]['place_id']
    return None

def get_place_details(place_id, api_key):
    url = f'https://maps.googleapis.com/maps/api/place/details/json'
    params = {
        'place_id': place_id,
        'key': api_key,
        'language': 'en'
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    if data['status'] == 'OK':
        result = data['result']
        name = result.get('name')
        address = result.get('formatted_address')
        return name, address
    return None, None

def crawl_google_map(query, max_places=10, force_english_api=False):
    print("[DEBUG][GoogleMap] 함수 진입")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--lang=en-US")  # 영어로 강제
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    results = []
    try:
        url = f"https://www.google.com/maps/search/{query}?hl=en"  # 영어로 강제
        print("[DEBUG][GoogleMap] URL:", url)
        driver.get(url)
        time.sleep(4)
        items = driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK')
        print("[DEBUG][GoogleMap] items 개수:", len(items))
        for item in items[:max_places]:
            try:
                # 식당명 추출 (여러 셀렉터 시도)
                name = '-'
                try:
                    name = item.find_element(By.CSS_SELECTOR, 'a.hfpxzc').text
                    if not name.strip():
                        raise Exception
                except Exception:
                    try:
                        name = item.find_element(By.CSS_SELECTOR, 'div.qBF1Pd').text
                        if not name.strip():
                            raise Exception
                    except Exception:
                        try:
                            name = item.find_element(By.CSS_SELECTOR, 'span.DkEaL').text
                        except Exception:
                            name = '-'
                link = item.find_element(By.CSS_SELECTOR, 'a.hfpxzc').get_attribute('href')
                if '/maps/place/' not in link:
                    link = ''
                rating = item.find_element(By.CSS_SELECTOR, 'span.MW4etd').text if item.find_elements(By.CSS_SELECTOR, 'span.MW4etd') else '-'
                review_text = item.find_element(By.CSS_SELECTOR, 'span.UY7F9').text if item.find_elements(By.CSS_SELECTOR, 'span.UY7F9') else '-'
                review = re.sub(r'[^0-9]', '', review_text) if review_text != '-' else '-'
                # 구글 지도 주소/영업시간 분리
                spans = item.find_elements(By.CSS_SELECTOR, 'div.W4Efsd span')
                addr = '-'
                for s in spans:
                    txt = s.text.strip()
                    # 주소 패턴: 주소 키워드 + 숫자
                    if any(word in txt for word in ['시', '도', '구', '군', '동', '로', '길', '번지']) and any(char.isdigit() for char in txt):
                        addr = txt
                        break
                if addr == '-' and spans:
                    addr = spans[-1].text
                hours = '-'
                phone = '-'
                for s in spans:
                    txt = s.text.strip()
                    if re.match(r'\d{2,4}-\d{3,4}-\d{4}', txt):
                        phone = txt
                    elif any(word in txt for word in ['영업', '마감', '오픈', '오전', '오후', '시작', '종료']):
                        hours = txt
                if hours == '-' and phone != '-':
                    hours = phone
                price_match = re.search(r'₩[0-9,~\-,]+', addr)
                price = price_match.group(0) if price_match else '-'
                # 위도/경도 추출 (링크에서 추출 시도)
                lat, lng = None, None
                m = re.search(r'/@([0-9.]+),([0-9.]+),', link)
                if m:
                    lat, lng = float(m.group(1)), float(m.group(2))
                if (not lat or not lng) and addr and addr != '-':
                    # 한글 주소로도 재시도
                    lat, lng = geocode_google(addr)
                    if (not lat or not lng):
                        # 영문 주소라면 한글 주소로 변환 시도 (예: 'Seongsu-dong, Seoul' -> '서울 성수동')
                        # 실제 변환은 어렵지만, 예시로 변환 시도
                        if re.search(r'[a-zA-Z]', addr):
                            # 간단 변환 예시: 'Seongsu' -> '성수', 'Seoul' -> '서울'
                            addr_kr = addr.replace('Seoul', '서울').replace('Seongsu', '성수').replace('dong', '동').replace(' ', '')
                            lat, lng = geocode_google(addr_kr)
                        if (not lat or not lng):
                            print(f'[DEBUG][GoogleMap] Geocoding 실패: {addr}')
                # 영어 주소 API로 대체
                if force_english_api:
                    place_id = get_place_id(name, GOOGLE_API_KEY)
                    if place_id:
                        _, en_addr = get_place_details(place_id, GOOGLE_API_KEY)
                        if en_addr:
                            addr = en_addr
                results.append({
                    'platform': '구글지도',
                    'name': name,
                    'rating': rating,
                    'review': review,
                    'addr': addr,
                    'hours': hours,
                    'price': price,
                    'link': link,
                    'lat': lat,
                    'lng': lng
                })
            except Exception as e:
                print('[DEBUG][GoogleMap] Error:', e)
                continue
    except Exception as e:
        print('[DEBUG][GoogleMap] Main Error:', e)
    finally:
        driver.quit()
    return results

# 네이버 블로그 크롤링 함수 추가
def crawl_naver_blog(query, max_places=10):
    print("[DEBUG][NaverBlog] 함수 진입")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    url = f"https://search.naver.com/search.naver?where=post&query={query}"
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    items = soup.select('li.bx')
    print("[DEBUG][NaverBlog] items 개수:", len(items))
    results = []
    for item in items[:max_places]:
        try:
            title_tag = item.select_one('a.api_txt_lines.total_tit')
            name = title_tag.text.strip() if title_tag else '-'
            link = title_tag['href'] if title_tag and title_tag.has_attr('href') else ''
            desc_tag = item.select_one('div.api_txt_lines.dsc_txt')
            desc = desc_tag.text.strip() if desc_tag else '-'
            # 블로그 썸네일
            img_tag = item.select_one('img')
            photo = img_tag['src'] if img_tag and img_tag.has_attr('src') else None
            # 블로그에서 평점/리뷰/주소는 없을 수 있음
            results.append({
                'platform': '네이버블로그',
                'name': name,
                'rating': '-',
                'review': '-',
                'addr': desc,
                'hours': '-',
                'link': link,
                'photo': photo
            })
        except Exception as e:
            print('[DEBUG][NaverBlog] Error:', e)
            continue
    return results

# 주소를 좌표로 변환하는 함수 (카카오/구글)
def geocode_kakao(address):
    headers = {"Authorization": "KakaoAK 1554f15d9ddce23bec39c091798acb16"}
    url = f"https://dapi.kakao.com/v2/local/search/address.json?query={address}"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        if data['documents']:
            x = float(data['documents'][0]['x'])
            y = float(data['documents'][0]['y'])
            return y, x
    return None, None

def geocode_google(address):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_API_KEY}"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        if data['status'] == 'OK' and data['results']:
            loc = data['results'][0]['geometry']['location']
            return loc['lat'], loc['lng']
    return None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    print("[DEBUG] /search 라우트 진입")
    query = request.form.get('query', '맛집')
    lang = request.form.get('lang', 'ko')
    max_places = 10
    if lang == 'en':
        google_results = crawl_google_map(query, max_places, force_english_api=True)
        for r in google_results:
            r['platform'] = 'Google Maps'
        all_results = google_results
    else:
        kakao_results = crawl_kakao_map(query, max_places)
        google_results = crawl_google_map(query, max_places, force_english_api=False)
        all_results = kakao_results + google_results
    return jsonify({'success': True, 'restaurants': all_results})

server_thread = None
server_running = False

def run_server():
    global server_running
    server_running = True
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def stop_server():
    global server_running
    server_running = False
    # 서버 종료 로직
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

if __name__ == '__main__':
    # PC에서 실행할 때는 자동으로 브라우저 열기
    if not os.environ.get('ANDROID_DATA'):
        threading.Thread(target=lambda: webbrowser.open('http://localhost:5000')).start()
    run_server()