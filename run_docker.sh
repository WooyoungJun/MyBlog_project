echo killing old docker processes
sudo docker-compose rm -fs

echo building docker containers as daemon
sudo docker-compose up --build -d