#!/usr/bin/env sh
set -eu

STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p backups
tar -czf "backups/storage-${STAMP}.tar.gz" storage
echo "Storage backup created at backups/storage-${STAMP}.tar.gz"
