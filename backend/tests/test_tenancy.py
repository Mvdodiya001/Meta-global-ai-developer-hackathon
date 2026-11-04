"""Rewrite P1: tenancy columns, demo tenant, Postgres migration parity."""

import os
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from app import models
from app.db import get_engine_for_url, init_db, init_engine
from app.modules.identity import DEMO_TENANT_ID, ensure_tenant, tenant_query
from app.services import seed

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"


def test_tenant_defaults_and_seed(tmp_path: Path) -> None:
    """P1: rows default to the demo tenant; the seed creates it."""
    db = tmp_path / "tenant.db"
    seed.seed_demo(db, CORPUS_ROOT)
    session = sessionmaker(bind=init_db(db), future=True)()
    tenant = session.get(models.Tenant, DEMO_TENANT_ID)
    assert tenant is not None
    matter = session.get(models.Matter, "MAT-01")
    assert matter is not None and matter.tenant_id == DEMO_TENANT_ID
    fact = session.get(models.Fact, "F-LOOP-92")
    assert fact is not None and fact.tenant_id == DEMO_TENANT_ID
    scoped = tenant_query(sa.select(models.Fact), models.Fact, DEMO_TENANT_ID)
    rows = session.execute(scoped).scalars().all()
    assert len(rows) == 28  # 13 seeded + 15 understanding (Phase 1)
    other = tenant_query(sa.select(models.Fact), models.Fact, "other-tenant")
    assert session.execute(other).scalars().all() == []
    session.close()


def test_old_database_file_heals_missing_columns(tmp_path: Path) -> None:
    """Upload-500 regression: a DB file from before a schema change heals.

    `init_db` adds known additive columns to existing tables, so an old
    demo file works after an upgrade instead of 500ing on INSERT.
    """


    db = tmp_path / "old.db"
    seed.seed_demo(db, CORPUS_ROOT)
    engine = init_db(db)
    with engine.begin() as conn:
        conn.execute(sa.text("ALTER TABLE intake_jobs DROP COLUMN input_b64"))
    init_db(db)  # heal
    session = sessionmaker(bind=engine, future=True)()
    session.execute(
        sa.insert(models.IntakeJob).values(
            id="JOB-OLD",
            matter_id="MAT-01",
            kind="document_extract",
            status="queued",
            stage="queued",
            document_id=None,
            input_b64=None,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
    )
    session.commit()
    session.close()


def test_ensure_tenant_idempotent(tmp_path: Path) -> None:
    """P1: ensure_tenant creates once and reports the same id."""
    session = sessionmaker(bind=init_db(tmp_path / "t.db"), future=True)()
    assert ensure_tenant(session) == DEMO_TENANT_ID
    assert ensure_tenant(session) == DEMO_TENANT_ID
    count = session.execute(sa.select(sa.func.count()).select_from(models.Tenant)).scalar()
    assert count == 1
    session.close()


@pytest.mark.skipif(
    not os.environ.get("CLAUSETRACE_PG_URL"),
    reason="set CLAUSETRACE_PG_URL to run the Postgres parity test",
)
def test_sqlite_to_postgres_parity(tmp_path: Path) -> None:
    """P1: migrating the seeded demo to Postgres preserves every row."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "migrate", Path(__file__).resolve().parents[2] / "scripts" / "migrate_sqlite_to_postgres.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    db = tmp_path / "demo.db"
    seed.seed_demo(db, CORPUS_ROOT)
    counts = module.migrate(str(db), os.environ["CLAUSETRACE_PG_URL"])
    assert counts, "no tables migrated"
    for name, (source_count, target_count) in counts.items():
        assert target_count >= source_count, f"{name}: {source_count} -> {target_count}"
    # Spot-check evidence integrity on the Postgres side.
    engine = init_engine(get_engine_for_url(os.environ["CLAUSETRACE_PG_URL"]))
    session = sessionmaker(bind=engine, future=True)()
    fact = session.get(models.Fact, "F-LOOP-92")
    assert fact is not None and fact.tenant_id == DEMO_TENANT_ID
    session.close()
