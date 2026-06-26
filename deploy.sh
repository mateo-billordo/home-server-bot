#!/bin/bash
set -e
cd ~/home-server-bot
git pull

if [ "$1" = "--force" ]; then
    docker compose down
fi

docker compose build --no-cache
docker compose up -d
echo "✅ Deploy complete"
