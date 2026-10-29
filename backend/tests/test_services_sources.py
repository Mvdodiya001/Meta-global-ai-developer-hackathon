"""T1.2 tests: hashed snapshots, stable sha256, idempotent ingest, v2 + decoy."""

import hashlib
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.db import init_db
from app.services import sources

RAW_DIR = Path(__file__).resolve().parents[2] / "corpus" / "raw"


def make_session(tmp_path: Path) -> Session:
    """Open a fresh T1.1 database with a session (T1.2)."""
    engine = init_db(tmp_path / "sources.db")
    return sessionmaker(bind=engine, future=True)()


def count_rows(session: Session, entity: Any) -> int:
    """Count rows of one mapped table (T1.2)."""
    result = session.execute(sa.select(sa.func.count()).select_from(entity)).scalar()
    assert result is not None
    return int(result)


def test_load_corpus_versions_and_provisions(tmp_path: Path) -> None:
    """T1.2: Done when v1, v2 and decoy are loaded."""
    session = make_session(tmp_path)
    ids = sources.load_corpus(session, RAW_DIR)
    assert set(ids) == {
        "SV-DPDP-ACT-V1",
        "SV-DPDP-ACT-V2SIM",
        "SV-DPDP-RULES-V1",
        "SV-GSR-843E-V1",
        "SV-DECOY-V1",
    }
    assert count_rows(session, models.SourceVersion) == 5
    assert count_rows(session, models.Provision) == 5 + 5 + 4 + 1 + 1
    session.close()


def test_sha256_stable(tmp_path: Path) -> None:
    """T1.2: Done when stored sha256 values recompute stably."""
    session = make_session(tmp_path)
    sources.load_corpus(session, RAW_DIR)
    for version in session.execute(sa.select(models.SourceVersion)).scalars().all():
        digest = hashlib.sha256(version.raw_text.encode("utf-8")).hexdigest()
        assert digest == version.content_sha256
    for row in session.execute(sa.select(models.Provision)).scalars().all():
        digest = hashlib.sha256(row.text.encode("utf-8")).hexdigest()
        assert digest == row.text_sha256
    session.close()


def test_ingest_identical_content_is_idempotent(tmp_path: Path) -> None:
    """T1.2: Done when ingesting identical content adds no new version."""
    session = make_session(tmp_path)
    first = sources.load_corpus(session, RAW_DIR)
    second = sources.load_corpus(session, RAW_DIR)
    assert first == second
    assert count_rows(session, models.SourceVersion) == 5
    assert count_rows(session, models.Provision) == 16
    session.close()


def test_simulated_v2_links_to_v1(tmp_path: Path) -> None:
    """T1.2: v2 is labelled simulated and supersedes v1."""
    session = make_session(tmp_path)
    sources.load_corpus(session, RAW_DIR)
    v2 = sources.get_version(session, "SV-DPDP-ACT-V2SIM")
    assert v2.is_simulated is True
    assert v2.supersedes_id == "SV-DPDP-ACT-V1"
    v1_text = sources.get_version(session, "SV-DPDP-ACT-V1").raw_text
    assert v2.raw_text != v1_text
    session.close()


def test_decoy_source_loaded(tmp_path: Path) -> None:
    """T1.2: Done when the decoy source is loaded."""
    session = make_session(tmp_path)
    sources.load_corpus(session, RAW_DIR)
    decoy = session.execute(
        sa.select(models.Source).where(models.Source.id == "SRC-DECOY")
    ).scalar_one()
    assert "Emblems" in decoy.title
    rows = sources.list_provisions(session, "SV-DECOY-V1")
    assert [row.key for row in rows] == ["DECOY_Emblems-Act-1950_s3"]
    session.close()


def test_unknown_version_raises_source_unavailable(tmp_path: Path) -> None:
    """T1.2: lookups for missing versions raise a typed error."""
    session = make_session(tmp_path)
    sources.load_corpus(session, RAW_DIR)
    with pytest.raises(sources.SourceUnavailable):
        sources.get_version(session, "SV-NOPE")
    session.close()
