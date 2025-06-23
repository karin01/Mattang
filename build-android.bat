@echo off
echo ========================================
echo 맛탕 안드로이드 앱 빌드 시작
echo ========================================

echo 1. Node.js 패키지 설치 중...
call npm install

echo 2. Capacitor 초기화 중...
call npx cap init Mattang com.mattang.app

echo 3. 안드로이드 플랫폼 추가 중...
call npx cap add android

echo 4. 웹 파일 동기화 중...
call npx cap sync android

echo 5. Android Studio 열기...
call npx cap open android

echo ========================================
echo 빌드 준비 완료!
echo Android Studio에서 앱을 빌드하세요.
echo ========================================
pause 