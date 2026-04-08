#!/usr/bin/env sh
set -eu

docker compose -f docker-compose.yml --env-file .env.staging up --build -d
docker compose -f docker-compose.yml --env-file .env.staging ps
