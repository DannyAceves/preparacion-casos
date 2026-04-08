#!/usr/bin/env sh
set -eu

SEED="${1:-}"

docker compose up --build -d postgres redis api worker frontend

if [ "$SEED" = "--seed" ]; then
  docker compose --profile tools run --rm seed
fi

docker compose ps
