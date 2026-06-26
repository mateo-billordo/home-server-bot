#!/bin/bash
set -e
cd ~/home-server-bot
git pull
docker compose build --no-cache
docker compose up -d
echo "✅ Deploy complete"
