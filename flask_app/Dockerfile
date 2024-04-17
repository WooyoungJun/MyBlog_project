# flask app Dockerfile

# 베이스 이미지 선택
FROM python:3.10.12

# 작업 디렉토리 설정
RUN mkdir /flask_app
COPY . /flask_app
WORKDIR /flask_app

# 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# Port 명시
EXPOSE 8888