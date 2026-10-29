#!/bin/sh
# T1.4: wipe the demo database and re-seed it. Must finish in under 60 s.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
DB="${CLAUSETRACE_DB:-$ROOT/backend/db.sqlite3}"
rm -f "$DB" "$DB-wal" "$DB-shm" "$DB-journal"
START=$(date +%s)
"$ROOT/backend/.venv/bin/python" "$ROOT/scripts/seed_demo.py" --db "$DB"
END=$(date +%s)
echo "reset-demo done in $((END - START))s"
