# 맛탕 안드로이드 앱 빌드 가이드

## 📱 개요
맛탕 웹앱을 Capacitor를 사용하여 안드로이드 네이티브 앱으로 변환합니다.

## 🛠️ 사전 요구사항

### 1. Node.js 설치
- Node.js 16.x 이상 버전 필요
- [Node.js 공식 사이트](https://nodejs.org/)에서 다운로드

### 2. Android Studio 설치
- Android Studio 4.0 이상 버전 필요
- [Android Studio 공식 사이트](https://developer.android.com/studio)에서 다운로드
- Android SDK 설치 (API Level 21 이상)

### 3. Java Development Kit (JDK)
- JDK 8 또는 11 설치
- JAVA_HOME 환경변수 설정

## 🚀 빌드 과정

### Windows 사용자
```bash
# 배치 파일 실행
build-android.bat
```

### Linux/Mac 사용자
```bash
# 실행 권한 부여
chmod +x build-android.sh

# 스크립트 실행
./build-android.sh
```

### 수동 빌드
```bash
# 1. Node.js 패키지 설치
npm install

# 2. Capacitor 초기화
npx cap init Mattang com.mattang.app

# 3. 안드로이드 플랫폼 추가
npx cap add android

# 4. 웹 파일 동기화
npx cap sync android

# 5. Android Studio 열기
npx cap open android
```

## 📱 Android Studio에서 빌드

1. **Android Studio 열기**
   - 빌드 스크립트 실행 후 자동으로 열림
   - 또는 `npx cap open android` 명령어로 수동 열기

2. **프로젝트 동기화**
   - Android Studio에서 Gradle 동기화 실행
   - 필요한 SDK 다운로드 확인

3. **앱 빌드**
   - `Build > Build Bundle(s) / APK(s) > Build APK(s)` 선택
   - 또는 `Build > Generate Signed Bundle / APK` 선택 (배포용)

4. **APK 파일 위치**
   - `android/app/build/outputs/apk/debug/app-debug.apk`

## ⚙️ 앱 설정

### 앱 아이콘 변경
1. `android/app/src/main/res/` 폴더의 아이콘 파일들 교체
2. 다양한 해상도별 아이콘 제공 필요

### 앱 이름 변경
1. `android/app/src/main/res/values/strings.xml` 파일 수정
2. `app_name` 값 변경

### 권한 설정
- 위치 정보: `android.permission.ACCESS_FINE_LOCATION`
- 인터넷: `android.permission.INTERNET`
- 네트워크 상태: `android.permission.ACCESS_NETWORK_STATE`

## 🔧 환경변수 설정

### API 키 설정
```bash
# .env 파일 생성
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
KAKAO_REST_API_KEY=your_kakao_rest_api_key
```

### Android에서 환경변수 사용
1. `android/app/src/main/java/com/mattang/app/MainActivity.java` 파일 수정
2. 환경변수를 앱에서 읽을 수 있도록 설정

## 📦 배포 준비

### 디버그 APK
- 개발 및 테스트용
- 서명되지 않은 APK

### 릴리즈 APK
- Google Play Store 배포용
- 서명된 APK 필요
- ProGuard 설정 권장

### AAB (Android App Bundle)
- Google Play Store 권장 형식
- 더 작은 파일 크기
- 디바이스별 최적화

## 🐛 문제 해결

### 일반적인 오류

1. **Gradle 동기화 실패**
   ```bash
   # Gradle 캐시 정리
   cd android
   ./gradlew clean
   ```

2. **SDK 경로 오류**
   - Android Studio > Settings > Appearance & Behavior > System Settings > Android SDK
   - SDK 경로 확인 및 수정

3. **권한 오류**
   - `android/app/src/main/AndroidManifest.xml` 파일에서 권한 확인
   - 런타임 권한 요청 코드 확인

4. **네트워크 오류**
   - `android/app/src/main/AndroidManifest.xml`에서 인터넷 권한 확인
   - HTTP 통신 허용 설정 확인

### 로그 확인
```bash
# 안드로이드 로그 확인
adb logcat | grep "Mattang"
```

## 📱 앱 테스트

### 에뮬레이터 테스트
1. Android Studio에서 AVD Manager 열기
2. 에뮬레이터 생성 및 실행
3. 앱 설치 및 테스트

### 실제 디바이스 테스트
1. USB 디버깅 활성화
2. 디바이스 연결
3. 앱 설치 및 테스트

## 🔄 업데이트

### 웹 코드 변경 후
```bash
# 웹 파일 동기화
npx cap sync android

# Android Studio에서 다시 빌드
```

### Capacitor 플러그인 추가 후
```bash
# 플러그인 설치
npm install @capacitor/plugin-name

# 안드로이드에 플러그인 추가
npx cap sync android
```

## 📚 추가 리소스

- [Capacitor 공식 문서](https://capacitorjs.com/docs)
- [Android 개발자 가이드](https://developer.android.com/guide)
- [Google Play Console](https://play.google.com/console)

## 🆘 지원

문제가 발생하면 다음을 확인하세요:
1. 모든 사전 요구사항 설치 확인
2. 환경변수 설정 확인
3. 권한 설정 확인
4. 로그 파일 확인 