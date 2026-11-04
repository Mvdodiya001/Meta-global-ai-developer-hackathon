"""T1.1: SQLite engine (WAL), schema creation, append-only triggers.

Append-only tables (`findings`, `source_versions`, `provisions`, `audit_log`)
reject every UPDATE and DELETE at the database level (F7, F11, F14); state
changes are new rows in `finding_events`. Real paths must use `init_db`;
tests use a `tmp_path` file through the same function.

No `PRAGMA foreign_keys=ON` here on purpose (T1.2): with SQLAlchemy 2.1.6 /
Python 3.12 pysqlite, enabling it from a `connect` listener breaks combined
ORM flushes — the parent INSERT is dropped from the flush plan and the child
fails loudly (reproduced with zero app code: two mapped tables, one listener,
one commit). WAL mode is unaffected. Foreign-key validity is enforced by the
service layer instead (parents are written first; lookups raise typed errors
such as `SourceUnavailable`).
"""

import os
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from sqlalchemy.engine import Engine

from app.models import Base

APPEND_ONLY_TABLES = ("findings", "source_versions", "provisions", "audit_log")

ALL_TABLES = (
    "tenants",
    "users",
    "matters",
    "matter_context",
    "sources",
    "source_versions",
    "provisions",
    "rule_cards",
    "documents",
    "document_versions",
    "clauses",
    "facts",
    "claims",
    "findings",
    "finding_events",
    "challenger_reports",
    "edges",
    "runs",
    "tool_calls",
    "llm_calls",
    "reviews",
    "audit_log",
    "intake_jobs",
)


def trigger_ddl(table: str, operation: str) -> sa.TextClause:
    """Build the append-only trigger DDL for one table and operation (T1.1)."""
    return sa.text(
        f"CREATE TRIGGER IF NOT EXISTS {table}_no_{operation.lower()} "
        f"BEFORE {operation} ON {table} "
        f"BEGIN SELECT RAISE(ABORT, '{table} is append-only'); END;"
    )


def default_db_path() -> Path:
    """Demo database path: `$CLAUSETRACE_DB`, else gitignored `backend/db.sqlite3` (T1.4)."""
    override = os.environ.get("CLAUSETRACE_DB")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[1] / "db.sqlite3"


def get_engine(path: str | Path) -> Engine:
    """Open a SQLite engine with WAL mode and foreign keys enforced (T1.1).

    NullPool: a pooled SQLite connection keeps the old inode alive when
    `make reset-demo` replaces the database file, so later checkouts can
    read/write a deleted database and post-commit refreshes then fail
    with ObjectDeletedError (approve-500). Every checkout must open the
    file as it exists now.
    """
    engine = sa.create_engine(f"sqlite:///{path}", poolclass=sa.pool.NullPool)

    @sa.event.listens_for(engine, "connect")
    def _set_pragmas(dbapi_conn: Any, _: Any) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.close()

    return engine


def database_url() -> str:
    """Database URL for this process (Rewrite P1).

    `CLAUSETRACE_DB_URL` (any SQLAlchemy URL, e.g. PostgreSQL) wins;
    otherwise the demo SQLite file. Demo behaviour is unchanged.
    """
    override = os.environ.get("CLAUSETRACE_DB_URL")
    if override:
        return override
    return f"sqlite:///{default_db_path()}"


def get_engine_for_url(url: str) -> Engine:
    """Engine for any SQLAlchemy URL; SQLite files keep NullPool (P1)."""
    if url.startswith("sqlite"):
        return sa.create_engine(url, poolclass=sa.pool.NullPool)
    return sa.create_engine(url, pool_pre_ping=True)


ADDITIVE_COLUMNS: dict[str, list[tuple[str, str]]] = {
    # Columns added after tables first shipped. init_engine adds any that
    # an older database file is missing, so a demo DB created before a
    # schema change keeps working instead of 500ing on INSERT.
    "intake_jobs": [("input_b64", "TEXT")],
    "matters": [("tenant_id", "TEXT NOT NULL DEFAULT 'demo'")],
    "documents": [("tenant_id", "TEXT NOT NULL DEFAULT 'demo'")],
    "facts": [("tenant_id", "TEXT NOT NULL DEFAULT 'demo'")],
    "claims": [("tenant_id", "TEXT NOT NULL DEFAULT 'demo'")],
    "findings": [("tenant_id", "TEXT NOT NULL DEFAULT 'demo'")],
    "audit_log": [("tenant_id", "TEXT NOT NULL DEFAULT 'demo'")],
}


def ensure_columns(engine: Engine) -> None:
    """ADD any known additive columns missing from an older file (P-C).

    SQLite and Postgres both accept ADD COLUMN for these; Postgres uses
    IF NOT EXISTS. Tables themselves come from create_all.
    """
    with engine.begin() as conn:
        for table, columns in ADDITIVE_COLUMNS.items():
            if engine.dialect.name == "sqlite":
                existing = {
                    row[1]
                    for row in conn.execute(sa.text(f"PRAGMA table_info({table})"))
                }
            else:
                existing = {
                    row[0]
                    for row in conn.execute(
                        sa.text(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_name = :table"
                        ),
                        {"table": table},
                    )
                }
            for name, ddl in columns:
                if name not in existing:
                    guard = "IF NOT EXISTS " if engine.dialect.name != "sqlite" else ""
                    conn.execute(
                        sa.text(f"ALTER TABLE {table} ADD COLUMN {guard}{name} {ddl}")
                    )


def init_engine(engine: Engine) -> Engine:
    """Create tables + append-only triggers on an engine (P1).

    Triggers are SQLite/Postgres-compatible (BEFORE UPDATE/DELETE with
    RAISE is SQLite syntax; on Postgres the DDL is skipped and
    append-only is enforced by the service layer until P2 adds
    Postgres-native rules).
    """
    Base.metadata.create_all(engine)
    ensure_columns(engine)
    if engine.dialect.name == "sqlite":
        with engine.begin() as conn:
            for table in APPEND_ONLY_TABLES:
                for operation in ("UPDATE", "DELETE"):
                    conn.execute(trigger_ddl(table, operation))
    return engine


def init_db(path: str | Path) -> Engine:
    """Create all §2 tables plus append-only triggers; return the engine (T1.1)."""
    return init_engine(get_engine(path))
