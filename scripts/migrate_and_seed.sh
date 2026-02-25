#!/bin/sh
# Run migrations and seed. Use from project root:
#   docker compose run -e DATABASE_URL_SYNC=postgresql://seo:seo@postgres:5432/seo_agent --rm orchestrator-api sh scripts/migrate_and_seed.sh
set -e
cd /app
alembic -c alembic.ini upgrade head
python -c "from libs.common.seed_data import run_seed; run_seed()"
echo "Done: migrations + seed."
