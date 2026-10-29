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
    """Open a SQLite engine with WAL mode and foreign keys enforced (T1.1)."""
    engine = sa.create_engine(f"sqlite:///{path}")

    @sa.event.listens_for(engine, "connect")
    def _set_pragmas(dbapi_conn: Any, _: Any) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.close()

    return engine


def init_db(path: str | Path) -> Engine:
    """Create all §2 tables plus append-only triggers; return the engine (T1.1)."""
    engine = get_engine(path)
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        for table in APPEND_ONLY_TABLES:
            for operation in ("UPDATE", "DELETE"):
                conn.execute(trigger_ddl(table, operation))
    return engine
