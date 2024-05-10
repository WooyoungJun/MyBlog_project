#!/bin/bash

echo killing old docker processes
docker compose rm -fs

echo building docker containers as daemon
docker compose up --build -d

# Flask 애플리케이션 컨테이너의 ID 가져오기
FLASK_CONTAINER_ID=$(docker ps -qf "name=flask_app")

echo "Flask application container ID: $FLASK_CONTAINER_ID"
# 컨테이너 내부에서 migrate와 upgrade 명령 실행
# docker exec $FLASK_CONTAINER_ID flask db init
docker exec $FLASK_CONTAINER_ID flask db migrate
docker exec $FLASK_CONTAINER_ID flask db upgrade

# echo "update all model instances"
# docker exec $FLASK_CONTAINER_ID flask update_all_model_instances
