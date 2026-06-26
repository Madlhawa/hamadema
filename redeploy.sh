#!/bin/bash
set -e

echo "=========================================="
echo " Pulling latest changes from Git..."
echo "=========================================="
git pull origin main

echo "=========================================="
echo " Checking Environment Variables..."
echo "=========================================="
# Prompt for proxy credentials if they were introduced in a new update and are missing from .env
if [ -f .env ] && ! grep -q "PROXY_USERNAME" .env; then
    echo "New proxy configuration is missing from your .env file."
    read -p "Enter Decodo Proxy Username (e.g., spgqueytu9): " DECODO_USER
    read -p "Enter Decodo Proxy Password: " DECODO_PASS
    echo "PROXY_USERNAME=$DECODO_USER" >> .env
    echo "PROXY_PASSWORD=$DECODO_PASS" >> .env
    echo "PROXY_HOST=gate.decodo.com" >> .env
    echo "PROXY_PORT=10001" >> .env
    echo "Proxy variables appended to .env."
fi

echo "=========================================="
echo " Rebuilding and restarting Docker containers..."
echo "=========================================="
# Rebuild any containers whose code has changed
sudo docker-compose up -d --build

echo "=========================================="
echo " Cleaning up old Docker images..."
echo "=========================================="
# Frees up space on your VPS by removing old dangling image builds
sudo docker image prune -f

echo "=========================================="
echo " Redeploy complete!"
echo "=========================================="
