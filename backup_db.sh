#!/usr/bin/env bash
# Backup BD antes de cada deploy. NUNCA borra nada.
set -euo pipefail

STAMP=$(date +%F_%H%M%S)
OUT="backup_${STAMP}.sql.gz"

docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U "${POSTGRES_USER:-postgres}" "${POSTGRES_DB:-growthOS}" | gzip > "$OUT"

echo "Backup OK -> $OUT"
