echo killing old docker processes
docker-compose rm -fs

echo building docker containers as daemon
docker-compose up --build -d