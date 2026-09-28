#!/bin/sh
# Nisja e API-t brenda Docker-it.
#
# Qëllimi: `docker compose up` nga një clone i pastër të japë një
# sistem të përdorshëm pa hapa manualë. Prandaj këtu presim bazën,
# aplikojmë migrimet dhe mbushim të dhënat demo para se të nisim
# serverin. Të gjitha janë idempotente.

set -e

echo "[entrypoint] Po pres PostgreSQL-në..."

# Alembic-u dështon nëse baza ende nuk pranon lidhje. Provojmë deri
# në 60 sekonda para se të dorëzohemi.
attempt=0

until python -c "
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

try:
    engine = create_engine(settings.database_url)
    with engine.connect() as connection:
        connection.execute(text('SELECT 1'))
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    attempt=$((attempt + 1))

    if [ "$attempt" -ge 30 ]; then
        echo "[entrypoint] PostgreSQL nuk u përgjigj. Po ndalem."
        exit 1
    fi

    sleep 2
done

echo "[entrypoint] Po aplikoj migrimet..."
alembic upgrade head

# Para seed-it: dokumentet demo të shënuara FAILED i ri-indekson vetë
# seed-i; të tjerat i sheh administratori me arsyen te paneli.
echo "[entrypoint] Po kontrolloj dokumentet e ndërprera..."
python -m scripts.recover_documents

if [ "${SEED_ON_STARTUP:-1}" = "1" ]; then
    echo "[entrypoint] Po mbush të dhënat demo..."

    # Seed-i nuk duhet ta bllokojë nisjen: nëse Qdrant-i ende nuk
    # është gati, dokumentet mbeten PENDING dhe administratori i
    # ri-indekson nga paneli.
    python -m scripts.seed || \
        echo "[entrypoint] KUJDES: seed-i dështoi, API-ja niset gjithsesi."
fi

echo "[entrypoint] Po nis API-në."

exec "$@"
