# Python 3.9 기반 이미지 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 종속성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 포트 환경 변수 사용
ENV PORT=8080

# Flask 앱 실행
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app