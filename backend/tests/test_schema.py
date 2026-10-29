"""T1.1 tests (written first): §2 tables exist; append-only triggers raise."""

import pytest
import sqlalchemy as sa

from app import models
from app.db import ALL_TABLES, init_db


def seed_minimal(conn: sa.Connection) -> None:
    """Insert one parent chain plus one row per append-only table (T1.1)."""
    conn.execute(
        sa.insert(models.Matter).values(id="M-1", client_name="Acme", title="T")
    )
    conn.execute(
        sa.insert(models.Document).values(
            id="D-1", matter_id="M-1", title="DPA", kind="dpa"
        )
    )
    conn.execute(
        sa.insert(models.DocumentVersion).values(
            id="DV-1", document_id="D-1", text="t", sha256="s", created_at="2026-01-01T00:00:00Z"
        )
    )
    conn.execute(
        sa.insert(models.Clause).values(
            id="CL-1",
            document_version_id="DV-1",
            ref="9.2",
            heading="h",
            text="t",
            span_start=0,
            span_end=1,
        )
    )
    conn.execute(
        sa.insert(models.Claim).values(
            id="C-1",
            matter_id="M-1",
            clause_id="CL-1",
            claim_type="CT1",
            params_json={},
            question_text="q",
            as_of="2025-10-01",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    conn.execute(
        sa.insert(models.Finding).values(
            id="FND-1",
            claim_id="C-1",
            version_no=1,
            status="FOLLOWS",
            confidence_band="high",
            proof_json={},
            as_of="2025-10-01",
            source_version_ids_json=[],
            premise_ids_json=[],
            rule_card_ids_json=[],
            checker_report_json={},
            created_at="2026-01-01T00:00:00Z",
        )
    )
    conn.execute(
        sa.insert(models.Source).values(
            id="SRC-1", key="k", title="t", publisher="p", url="u", jurisdiction="IN"
        )
    )
    conn.execute(
        sa.insert(models.SourceVersion).values(
            id="SV-1",
            source_id="SRC-1",
            version_label="v1",
            published_on="2023-08-11",
            effective_from="2025-10-01",
            content_sha256="s",
            raw_text="t",
            is_simulated=False,
        )
    )
    conn.execute(
        sa.insert(models.Provision).values(
            id="PRV-1",
            source_version_id="SV-1",
            key="Section 6",
            text="t",
            text_sha256="s",
            effective_from="2025-10-01",
        )
    )
    conn.execute(
        sa.insert(models.AuditLog).values(
            id="AUD-1",
            ts="2026-01-01T00:00:00Z",
            actor_type="system",
            actor_id="system",
            event="seed",
            object_type="matter",
            object_id="M-1",
            details_json={},
        )
    )


def test_all_section2_tables_exist(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """T1.1: Done when all tables from DATA_MODEL_API §2 exist."""
    engine = init_db(tmp_path / "t.db")
    assert set(ALL_TABLES) <= set(sa.inspect(engine).get_table_names())


UPDATE_CASES = [
    ("findings", "FND-1", "status", "RULED_OUT"),
    ("source_versions", "SV-1", "version_label", "vX"),
    ("provisions", "PRV-1", "text", "changed"),
    ("audit_log", "AUD-1", "event", "rewritten"),
]


@pytest.mark.parametrize(("table", "row_id", "column", "value"), UPDATE_CASES)
def test_update_raises(tmp_path, table, row_id, column, value) -> None:  # type: ignore[no-untyped-def]
    """T1.1: UPDATE on an append-only table raises."""
    engine = init_db(tmp_path / "t.db")
    with engine.begin() as conn:
        seed_minimal(conn)
    stmt = sa.text(f"UPDATE {table} SET {column} = :v WHERE id = :i")
    with pytest.raises(sa.exc.DBAPIError, match="append-only"):
        with engine.begin() as conn:
            conn.execute(stmt, {"v": value, "i": row_id})


DELETE_CASES = [
    ("findings", "FND-1"),
    ("source_versions", "SV-1"),
    ("provisions", "PRV-1"),
    ("audit_log", "AUD-1"),
]


@pytest.mark.parametrize(("table", "row_id"), DELETE_CASES)
def test_delete_raises(tmp_path, table, row_id) -> None:  # type: ignore[no-untyped-def]
    """T1.1: DELETE on an append-only table raises."""
    engine = init_db(tmp_path / "t.db")
    with engine.begin() as conn:
        seed_minimal(conn)
    with pytest.raises(sa.exc.DBAPIError, match="append-only"):
        with engine.begin() as conn:
            conn.execute(sa.text(f"DELETE FROM {table} WHERE id = :i"), {"i": row_id})


def test_inserts_still_allowed(tmp_path) -> None:
    """T1.1: append-only blocks mutation, not new rows."""
    engine = init_db(tmp_path / "t.db")
    with engine.begin() as conn:
        seed_minimal(conn)
        conn.execute(
            sa.insert(models.AuditLog).values(
                id="AUD-2",
                ts="2026-01-02T00:00:00Z",
                actor_type="system",
                actor_id="system",
                event="seed2",
                object_type="matter",
                object_id="M-1",
                details_json={},
            )
        )
        count = conn.execute(sa.text("SELECT COUNT(*) FROM audit_log")).scalar()
    assert count == 2
