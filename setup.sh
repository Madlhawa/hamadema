#!/bin/bash
set -e

echo "=========================================="
echo " Lanka Aggregator - VPS Setup Script"
echo "=========================================="

# 1. Update and install dependencies
echo "[1/4] Updating system and installing dependencies..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git

# 2. Install Docker and Docker Compose
echo "[2/4] Installing Docker and Docker Compose..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
else
    echo "Docker is already installed."
fi

if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose is already installed."
fi

# 3. Setup Environment Variables
echo "[3/4] Configuring Environment Variables..."
if [ ! -f .env ]; then
    echo "Creating .env file..."
    read -p "Enter a secure PostgreSQL Password: " POSTGRES_PASS
    read -p "Enter a secure Meilisearch Master Key: " MEILI_KEY

    echo "POSTGRES_PASSWORD=$POSTGRES_PASS" > .env
    echo "MEILI_MASTER_KEY=$MEILI_KEY" >> .env
    echo ".env file created securely."
else
    echo ".env file already exists. Skipping..."
fi

# 4. Start the Application
echo "[4/4] Building and starting Docker containers..."
# Clean up any old containers/volumes safely before rebuilding
sudo docker-compose down -v || true
sudo docker-compose up -d --build

echo "=========================================="
echo " Setup Complete!"
echo " Your application is now running in the background."
echo " -> Access the UI: http://<YOUR_DROPLET_IP>"
echo " -> View live logs: docker-compose logs -f"
echo "=========================================="
