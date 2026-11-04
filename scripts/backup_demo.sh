#!/bin/sh
# Phase 6: back up the demo database (and optionally the cassette store).
#
#   sh scripts/backup_demo.sh [--cassettes]
#
# Postgres (CLAUSETRACE_DB_URL set): pg_dump from the compose container
# (or a local pg_dump when present). SQLite (default): file copy of
# backend/db.sqlite3 plus WAL sidecars when present.
# Output: backups/<UTC timestamp>/ with a manifest.txt.
# Restore (Postgres):  psql "$CLAUSETRACE_DB_URL" < backups/<ts>/db.sql
# Restore (SQLite):    cp backups/<ts>/db.sqlite3 backend/db.sqlite3
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$ROOT/backups/$TS"
mkdir -p "$OUT"

case "${CLAUSETRACE_DB_URL:-}" in
  ""|sqlite*)
    DB="${CLAUSETRACE_DB:-$ROOT/backend/db.sqlite3}"
    cp "$DB" "$OUT/db.sqlite3"
    for sidecar in "$DB-wal" "$DB-shm"; do
      [ -f "$sidecar" ] && cp "$sidecar" "$OUT/$(basename "$sidecar")" || true
    done
    echo "sqlite file copy of $DB" > "$OUT/manifest.txt"
    ;;
  *)
    if command -v pg_dump >/dev/null 2>&1; then
      PGURL="$(printf %s "$CLAUSETRACE_DB_URL" | sed 's/+psycopg//; s/+pg8000//')"
      pg_dump "$PGURL" > "$OUT/db.sql"
    else
      (cd "$ROOT" && docker compose exec -T postgres \
        pg_dump -U clausetrace clausetrace) > "$OUT/db.sql"
    fi
    echo "pg_dump of compose Postgres" > "$OUT/manifest.txt"
    ;;
esac

if [ "${1:-}" = "--cassettes" ]; then
  tar -czf "$OUT/cassettes.tgz" -C "$ROOT" corpus/cassettes
  echo "cassettes included" >> "$OUT/manifest.txt"
fi

echo "backup written to $OUT"
