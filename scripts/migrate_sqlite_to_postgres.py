"""Migrate a seeded SQLite demo database to Postgres (Rewrite P1).

Usage:
  CLAUSETRACE_PG_URL=postgresql+psycopg://user:pass@host:5432/db \
    backend/.venv/bin/python scripts/migrate_sqlite_to_postgres.py [sqlite-path]

Copies every table in `app.db.ALL_TABLES` order, preserving ids and
hashes exactly. The target schema is created first (idempotent); rows
whose primary key already exists are skipped, so a re-run is a no-op.
Prints per-table source/target counts for the parity check.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import sqlalchemy as sa  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app import models  # noqa: E402
from app.db import ALL_TABLES, get_engine, get_engine_for_url, init_engine  # noqa: E402

TABLE_MODELS = {
    table.__tablename__: table for table in vars(models).values()
    if isinstance(table, type) and hasattr(table, "__tablename__")
}


def migrate(sqlite_path: str, pg_url: str) -> dict[str, tuple[int, int]]:
    """Copy all rows SQLite → Postgres; return {table: (source, target)}."""
    source = sessionmaker(bind=get_engine(sqlite_path), future=True)()
    target_engine = init_engine(get_engine_for_url(pg_url))
    target = sessionmaker(bind=target_engine, future=True)()
    counts: dict[str, tuple[int, int]] = {}
    try:
        for name in ALL_TABLES:
            model = TABLE_MODELS[name]
            rows = source.execute(sa.select(model)).scalars().all()
            existing = (
                set(target.execute(sa.select(model.id)).scalars().all())
                if hasattr(model, "id")
                else set()
            )
            for row in rows:
                data = {
                    col.name: getattr(row, col.name) for col in model.__table__.columns
                }
                if data.get("id") in existing:
                    continue
                target.execute(sa.insert(model).values(**data))
            target.commit()
            target_count = target.execute(
                sa.select(sa.func.count()).select_from(model)
            ).scalar() or 0
            counts[name] = (len(rows), int(target_count))
        return counts
    finally:
        source.close()
        target.close()


def main() -> None:
    """Run the migration and print the parity table (P1)."""
    pg_url = os.environ.get("CLAUSETRACE_PG_URL", "")
    if not pg_url:
        raise SystemExit("set CLAUSETRACE_PG_URL (e.g. postgresql+psycopg://...)")
    sqlite_path = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "backend" / "db.sqlite3")
    counts = migrate(sqlite_path, pg_url)
    bad = {k: v for k, v in counts.items() if v[0] != v[1]}
    for name, (src, dst) in counts.items():
        print(f"{name}: {src} -> {dst}")
    if bad:
        raise SystemExit(f"parity mismatch: {bad}")
    print("parity OK")


if __name__ == "__main__":
    main()
