"""T1.4: seed produces a labelled demo matter with 12 span-exact clauses, fast."""

import time
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from app import models
from app.db import init_db
from app.services import seed

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"


def test_seed_demo_matter_and_clauses(tmp_path: Path) -> None:
    """T1.4: matter, demo context rows and 12 clauses with exact spans."""
    db = tmp_path / "demo.db"
    started = time.monotonic()
    result = seed.seed_demo(db, CORPUS_ROOT)
    elapsed = time.monotonic() - started
    assert elapsed < 60
    assert result["matter_id"] == "MAT-01"
    assert result["clauses"] == 12

    session = sessionmaker(bind=init_db(db), future=True)()
    try:
        matter = session.get(models.Matter, "MAT-01")
        assert matter is not None
        assert "Acme" in matter.client_name
        contexts = session.execute(sa.select(models.MatterContext)).scalars().all()
        assert {row.kind for row in contexts} == {"hearing", "task"}
        assert {row.source_label for row in contexts} == {"demo data"}
        doc = session.get(models.DocumentVersion, "DOCV-01")
        assert doc is not None
        clauses = (
            session.execute(sa.select(models.Clause).order_by(models.Clause.id))
            .scalars()
            .all()
        )
        assert [row.ref for row in clauses] == seed.EXPECTED_REFS
        for row in clauses:
            assert doc.text[row.span_start : row.span_end] == row.text
        nine_two = [row for row in clauses if row.ref == "9.2"]
        assert len(nine_two) == 1
        assert "outside India" in nine_two[0].text
        assert len(result["versions"]) == 5
        assert len(result["cards"]) == 7
    finally:
        session.close()


def test_seed_is_idempotent(tmp_path: Path) -> None:
    """T1.4: re-running the seed keeps one copy of every row."""
    db = tmp_path / "demo.db"
    first = seed.seed_demo(db, CORPUS_ROOT)
    second = seed.seed_demo(db, CORPUS_ROOT)
    assert first == second
    engine = init_db(db)
    with engine.connect() as conn:
        for entity, want in (
            (models.Matter, 1),
            (models.Clause, 12),
            (models.SourceVersion, 5),
            (models.RuleCard, 7),
            (models.Fact, 13),
        ):
            count = conn.execute(
                sa.select(sa.func.count()).select_from(entity)
            ).scalar()
            assert count == want


def test_seed_extracts_doc01_facts_in_replay(tmp_path: Path) -> None:
    """G8: a reset seeds DOC-01 extraction facts from the replay cassette."""
    db = tmp_path / "demo.db"
    seed.seed_demo(db, CORPUS_ROOT)
    session = sessionmaker(bind=init_db(db), future=True)()
    try:
        facts = (
            session.execute(
                sa.select(models.Fact)
                .where(models.Fact.matter_id == "MAT-01")
                .order_by(models.Fact.id)
            )
            .scalars()
            .all()
        )
        by_id = {row.id: row for row in facts}
        assert "F-LOOP-92" in by_id
        seeded = [row for row in facts if row.id.startswith("F-SEED-")]
        assert len(seeded) == 12
        assert [row.id for row in seeded] == [f"F-SEED-{i:02d}" for i in range(1, 13)]
        clause_ids = {
            row.id
            for row in session.execute(sa.select(models.Clause)).scalars().all()
        }
        for row in seeded:
            assert row.trust_class == "document_extracted"
            assert row.origin == "extracted"
            assert row.clause_id in clause_ids
            assert row.statement
    finally:
        session.close()
