#!/bin/bash
set -e

echo "=========================================="
echo " Pulling latest changes from Git..."
echo "=========================================="
git pull origin main

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
