# flask app Dockerfile

# 베이스 이미지 선택
FROM python:3.8.8

# 작업 디렉토리 설정
RUN mkdir /flask_app
WORKDIR /flask_app

# 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 코드 복사
COPY ./blog ./blog
COPY app.py .

# Port 명시
EXPOSE 8888