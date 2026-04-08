#!/usr/bin/env sh
set -eu

STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p backups
docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-caseprep}" "${POSTGRES_DB:-caseprep}" > "backups/db-${STAMP}.sql"
echo "Database backup created at backups/db-${STAMP}.sql"
