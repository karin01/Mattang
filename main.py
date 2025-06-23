import subprocess
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify, send_from_directory
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
from datetime import datetime, timedelta
from flask_cors import CORS
from fake_useragent import UserAgent
import queue
import firebase_admin
from firebase_admin import credentials, firestore
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# # 패키지 자동 설치
# def install_packages():
#     packages = ['requests', 'beautifulsoup4', 'selenium', 'flask', 'webdriver_manager', 'geopy', 'flask-cors', 'fake-useragent', 'firebase-admin']
#     for package in packages:
#         try:
#             __import__(package)
#         except ImportError:
#             subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# install_packages()

# 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CRED_PATH = os.path.join(BASE_DIR, 'firebase-credentials.json')

# Firebase 초기화
try:
    cred = credentials.Certificate(CRED_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase 초기화 성공")
except Exception as e:
    print(f"Firebase 초기화 실패: {e}")
    db = None

# 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static') # static 폴더 경로 명시적 정의
app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR) # static 폴더를 루트로 설정
CORS(app)

# templates 디렉토리 생성
if not os.path.exists(TEMPLATE_DIR):
    os.makedirs(TEMPLATE_DIR)

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

# 망고플레이트 크롤링 함수
def crawl_mangoplate(query, max_places=10):
    print("[DEBUG][MangoPlate] 함수 진입")
    results = []
    try:
        ua = UserAgent()
        headers = {
            'User-Agent': ua.random,
            'Referer': 'https://www.mangoplate.com/'
        }
        url = f"https://www.mangoplate.com/search/{query}"
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')
        items = soup.select('section#contents div.list-restaurant-item')
        print(f"[DEBUG][MangoPlate] items 개수: {len(items)}")

        for item in items[:max_places]:
            try:
                name_tag = item.select_one('h2.title')
                name = name_tag.text.strip() if name_tag else '-'
                link_tag = item.select_one('a')
                link = 'https://www.mangoplate.com' + link_tag['href'] if link_tag and link_tag.has_attr('href') else ''
                rating_tag = item.select_one('strong.point')
                rating = rating_tag.text.strip() if rating_tag else '-'
                review_tag = item.select_one('span.review_count')
                review = review_tag.text.strip().replace('리뷰','').replace('Reviews','').strip() if review_tag else '-'
                addr_tag = item.select_one('p.etc')
                addr = addr_tag.text.strip() if addr_tag else '-'
                img_tag = item.select_one('img')
                photo = img_tag['data-original'] if img_tag and img_tag.has_attr('data-original') else (img_tag['src'] if img_tag and img_tag.has_attr('src') else None)
                results.append({
                    'platform': '망고플레이트',
                    'name': name,
                    'rating': rating,
                    'review': review,
                    'addr': addr,
                    'hours': '-',
                    'link': link,
                    'photo': photo,
                    'lat': None,
                    'lng': None
                })
            except Exception as e:
                print(f'[DEBUG][MangoPlate] 개별 아이템 파싱 오류: {e}')
                continue
    except requests.exceptions.RequestException as e:
        print(f"[MangoPlate] 망고플레이트 연결에 실패했습니다: {e}")
    except Exception as e:
        print(f"[MangoPlate] 알 수 없는 오류 발생: {e}")
        
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

def crawl_diningcode(query, max_places=10):
    print("[DEBUG][Diningcode] 함수 진입")
    results = []
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        url = f"https://www.diningcode.com/search?query={query}"
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul#search_list"))
        )

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        items = soup.select('ul#search_list > li')
        print(f"[DEBUG][Diningcode] items 개수: {len(items)}")

        for item in items[:max_places]:
            try:
                name_tag = item.select_one('a span.btxt')
                if not name_tag: continue

                name = name_tag.text.strip()
                link_tag = item.select_one('a')
                link = "https://www.diningcode.com" + (link_tag['href'] if link_tag else '')

                rating_tag = item.select_one('span.stxt > strong')
                rating = rating_tag.text.strip().replace('점', '') if rating_tag else '-'

                addr_tag = item.select_one('p.addr')
                addr = addr_tag.text.strip() if addr_tag else '-'
                
                category_tag = item.select_one('p.cat')
                category = category_tag.text.strip() if category_tag else ''

                photo_tag = item.select_one('div.R_Img img')
                photo = photo_tag['src'] if photo_tag and photo_tag.has_attr('src') else None

                results.append({
                    'platform': '다이닝코드',
                    'name': name,
                    'rating': rating,
                    'review': '-',
                    'addr': f"{addr} ({category})".strip(),
                    'hours': '-',
                    'link': link,
                    'photo': photo,
                    'lat': None,
                    'lng': None
                })
            except Exception as e:
                print(f'[DEBUG][Diningcode] 개별 아이템 파싱 오류: {e}')
                continue
    except Exception as e:
        print(f"[Diningcode] 알 수 없는 오류 발생: {e}")
    finally:
        if driver:
            driver.quit()
    return results

def crawl_siksin(query, max_places=10):
    print("[DEBUG][Siksin] 함수 진입")
    results = []
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        url = f"https://www.siksinhot.com/search?keywords={query}"
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.local_search_list"))
        )

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        items = soup.select('div.local_search_list > ul > li')
        print(f"[DEBUG][Siksin] items 개수: {len(items)}")

        for item in items[:max_places]:
            try:
                title_tag = item.select_one('strong.title > a')
                if not title_tag: continue
                
                name = title_tag.text.strip()
                link = "https://www.siksinhot.com" + title_tag['href']

                rating_tag = item.select_one('span.score')
                rating = rating_tag.text.strip() if rating_tag else '-'
                
                addr_tag = item.select_one('p.addr')
                addr = addr_tag.text.strip() if addr_tag else '-'

                photo_tag = item.select_one('div.img > a > img')
                photo = photo_tag['src'] if photo_tag and photo_tag.has_attr('src') else None

                results.append({
                    'platform': '식신',
                    'name': name,
                    'rating': rating,
                    'review': '-',
                    'addr': addr,
                    'hours': '-',
                    'link': link,
                    'photo': photo,
                    'lat': None,
                    'lng': None
                })
            except Exception as e:
                print(f'[DEBUG][Siksin] 개별 아이템 파싱 오류: {e}')
                continue
    except Exception as e:
        print(f"[Siksin] 알 수 없는 오류 발생: {e}")
    finally:
        if driver:
            driver.quit()
    return results

def get_normalized_key(name, addr):
    # 이름에서 공백과 특수문자 일부를 제거하고 소문자화
    norm_name = re.sub(r"[\s&'-]+", "", name).lower()
    
    # 주소에서 앞 2-3개의 주요 부분만 사용하여 키 생성 (시/도, 구/군, 동/읍/면)
    addr_parts = addr.split()[:3]
    norm_addr = "".join(addr_parts).lower()
    
    # 가게 이름이 주소의 일부를 포함하는 경우(도로명 주소 가게)도 고려
    for part in addr_parts:
        if part in norm_name:
            norm_name = norm_name.replace(part, "")

    return f"{norm_name}|{norm_addr}"

def deduplicate_and_merge_results(results):
    unique_restaurants = {}
    
    for r in results:
        if not r.get('name') or not r.get('addr') or not r.get('platform'):
            continue

        key = get_normalized_key(r['name'], r['addr'])
        
        try:
            rating_val = float(r.get('rating', 0))
        except (ValueError, TypeError):
            rating_val = 0.0
        
        try:
            review_str = str(r.get('review', '0')).replace(',', '').replace('리뷰', '').strip()
            review_val = int(re.sub(r'[^0-9]', '', review_str) or 0)
        except (ValueError, TypeError):
            review_val = 0

        if key not in unique_restaurants:
            unique_restaurants[key] = {
                'name': r['name'],
                'addr': r['addr'],
                'platforms': [r['platform']],
                'ratings': [rating_val] if rating_val > 0 else [],
                'reviews': [review_val],
                'links': {r['platform']: r.get('link')},
                'photo': r.get('photo'),
                'hours': r.get('hours', '-'),
                'lat': r.get('lat'),
                'lng': r.get('lng'),
            }
        else:
            existing = unique_restaurants[key]
            if r['platform'] not in existing['platforms']:
                existing['platforms'].append(r['platform'])
                if rating_val > 0:
                    existing['ratings'].append(rating_val)
                existing['reviews'].append(review_val)
                existing['links'][r['platform']] = r.get('link')

                if not existing.get('photo') and r.get('photo'):
                    existing['photo'] = r.get('photo')

    final_results = []
    for data in unique_restaurants.values():
        avg_rating = sum(data['ratings']) / len(data['ratings']) if data['ratings'] else 0.0
        total_reviews = sum(data['reviews'])
        
        primary_link = list(data['links'].values())[0] if data['links'] else ''

        final_results.append({
            'name': data['name'],
            'platform': data['platforms'],
            'rating': f"{avg_rating:.1f}" if avg_rating > 0 else '-',
            'review': str(total_reviews) if total_reviews > 0 else '-',
            'addr': data['addr'],
            'hours': data['hours'],
            'link': primary_link,
            'photo': data['photo'],
            'lat': data['lat'],
            'lng': data['lng'],
        })
        
    return final_results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    if not db:
        return jsonify({'success': False, 'message': '데이터베이스 연결에 실패했습니다. 서버 로그를 확인해주세요.'}), 500

    data = request.get_json()
    query = data.get('query')
    lang = data.get('lang', 'ko')
    if not query:
        return jsonify({'success': False, 'message': '검색어를 입력해주세요.'})

    # 고정 상점 정보
    fixed_store = {
        'platform': '고정광고',
        'name': '효제주물럭',
        'rating': '4.8',
        'review': '120',
        'addr': '서울 종로구 종로35길 44',
        'hours': '11:00~22:00',
        'link': 'https://www.google.com/maps/search/?api=1&query=효제주물럭',
        'photo': '/images/효제주물럭.png',
        'lat': 37.5731,
        'lng': 126.9978
    }

    # Firestore 캐시 로직
    try:
        # 6개월 이전의 오래된 캐시 삭제
        six_months_ago = datetime.now() - timedelta(days=180)
        cache_collection_ref = db.collection('search_cache')
        old_docs_query = cache_collection_ref.where('created_at', '<', six_months_ago)
        for doc in old_docs_query.stream():
            doc.reference.delete()

        # 캐시 확인
        cached_doc_ref = db.collection('search_cache').document(query)
        cached_doc = cached_doc_ref.get()

        if cached_doc.exists:
            print(f"'{query}'에 대한 Firestore 캐시된 결과 반환")
            cached_data = cached_doc.to_dict().get('results', [])
            final_results = [fixed_store] + cached_data
            return jsonify({'success': True, 'restaurants': final_results})
    except Exception as e:
        print(f"Firestore 캐시 처리 중 오류: {e}")

    print(f"'{query}'에 대한 실시간 검색 수행")

    results = []
    threads = []
    result_queue = queue.Queue()
    
    crawl_functions = [
        (crawl_naver_map, (query, 10 if lang == 'ko' else 0)),
        (crawl_kakao_map, (query, 10 if lang == 'ko' else 0)),
        # (crawl_mangoplate, (query, 10 if lang == 'ko' else 0)), # 망고플레이트 제외
        # (crawl_diningcode, (query, 10 if lang == 'ko' else 0)), # 다이닝코드 불안정하여 임시 비활성화
        # (crawl_siksin, (query, 10 if lang == 'ko' else 0)), # 식신 불안정하여 임시 비활성화
        (crawl_google_map, (query, 10 if lang == 'en' else 5, lang == 'en')),
    ]

    for func, args in crawl_functions:
        if args[1] > 0:
            thread = threading.Thread(target=lambda q, f, a: q.put(f(*a)), args=(result_queue, func, args))
            threads.append(thread)
            thread.start()

    for t in threads:
        t.join(timeout=60) 

    while not result_queue.empty():
        results.extend(result_queue.get())
        
    merged_results = deduplicate_and_merge_results(results)
    
    # 결과가 있을 경우 Firestore 캐시에 저장
    if merged_results:
        try:
            doc_ref = db.collection('search_cache').document(query)
            doc_ref.set({
                'query': query,
                'results': merged_results,
                'created_at': firestore.SERVER_TIMESTAMP
            })
            print(f"'{query}'에 대한 검색 결과를 Firestore 캐시에 저장")
        except Exception as e:
            print(f"Firestore 캐시 저장 중 오류: {e}")

    final_results = [fixed_store] + merged_results
    return jsonify({'success': True, 'restaurants': final_results})

server_thread = None
server_running = False

# 기존 if __name__ == "__main__": 블록 삭제
# run_server() 함수 수정
def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def stop_server():
    global server_running
    server_running = False
    # 서버 종료 로직
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def stop_server():
    global server_running
    server_running = False
    # 서버 종료 로직
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
