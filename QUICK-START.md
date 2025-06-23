# 🚀 맛탕 안드로이드 앱 - 빠른 시작 가이드

## 📋 사전 준비

### 필수 설치 항목
1. **Node.js** (16.x 이상)
2. **Android Studio** (4.0 이상)
3. **Java JDK** (8 또는 11)

### 환경 설정
- Android SDK 설치 (API Level 21 이상)
- JAVA_HOME 환경변수 설정

## ⚡ 빠른 빌드

### Windows
```bash
# 배치 파일 실행
build-android.bat
```

### Linux/Mac
```bash
# 실행 권한 부여 후 실행
chmod +x build-android.sh
./build-android.sh
```

## 📱 APK 생성

1. **Android Studio 열기**
   - 빌드 스크립트 실행 후 자동으로 열림

2. **Gradle 동기화**
   - Android Studio에서 자동으로 실행됨

3. **APK 빌드**
   - `Build` → `Build Bundle(s) / APK(s)` → `Build APK(s)`

4. **APK 파일 위치**
   ```
   android/app/build/outputs/apk/debug/app-debug.apk
   ```

## 🔧 주요 설정

### API 키 설정
```bash
# .env 파일 생성
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
KAKAO_REST_API_KEY=your_kakao_rest_api_key
```

### 앱 정보 수정
- 앱 이름: `android/app/src/main/res/values/strings.xml`
- 앱 아이콘: `android/app/src/main/res/` 폴더의 아이콘 파일들

## 🐛 문제 해결

### Gradle 오류
```bash
cd android
./gradlew clean
./gradlew build
```

### SDK 오류
- Android Studio → Settings → Android SDK
- 필요한 SDK 설치

### 권한 오류
- `android/app/src/main/AndroidManifest.xml` 확인
- 런타임 권한 요청 코드 확인

## 📚 자세한 가이드

더 자세한 내용은 `README-Android.md` 파일을 참조하세요.

## 🆘 지원

문제가 발생하면:
1. 모든 사전 요구사항 설치 확인
2. 환경변수 설정 확인
3. 권한 설정 확인
4. 로그 파일 확인 