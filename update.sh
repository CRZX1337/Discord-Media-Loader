#!/bin/bash

echo "🚀 Starting Bot Update..."

# 1. Pull latest code from GitHub
echo "📥 Pulling the latest version from the repository..."
git pull

# 2. Build Docker images completely fresh (no cache)
echo "🏗️ Rebuilding Docker containers..."
sudo docker compose build --no-cache

# 3. Start/Update the Docker container in the background
echo "🟢 Starting up the Bot..."
sudo docker compose up -d

echo "✅ Update completed successfully! The bot is now running the latest version! 🎉"
