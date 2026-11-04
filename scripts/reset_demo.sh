#!/bin/sh
# T1.4: wipe the demo database and re-seed it. Must finish in under 60 s.
# SQLite (default): delete the files and re-seed by path.
# Postgres (`CLAUSETRACE_DB_URL` set to a non-sqlite URL): drop the schema,
# recreate it, then re-seed through the same URL.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
DB="${CLAUSETRACE_DB:-$ROOT/backend/db.sqlite3}"
START=$(date +%s)
case "${CLAUSETRACE_DB_URL:-}" in
  ""|sqlite*)
    rm -f "$DB" "$DB-wal" "$DB-shm" "$DB-journal"
    "$ROOT/backend/.venv/bin/python" "$ROOT/scripts/seed_demo.py" --db "$DB"
    ;;
  *)
    "$ROOT/backend/.venv/bin/python" - "$ROOT" <<'PY'
import os
import sys
sys.path.insert(0, sys.argv[1] + "/backend")
from app.db import get_engine_for_url, init_engine
from app.models import Base
engine = get_engine_for_url(os.environ["CLAUSETRACE_DB_URL"])
Base.metadata.drop_all(engine)
init_engine(engine)
PY
    "$ROOT/backend/.venv/bin/python" "$ROOT/scripts/seed_demo.py"
    ;;
esac
END=$(date +%s)
echo "reset-demo done in $((END - START))s"
