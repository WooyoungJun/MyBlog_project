# nginx Dockerfile

# 베이스 이미지 선택
FROM nginx:1.18.0

# 새로운 conf 파일로 업데이트
RUN rm /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/
RUN rm /etc/nginx/conf.d/default.conf
COPY default.conf /etc/nginx/conf.d	