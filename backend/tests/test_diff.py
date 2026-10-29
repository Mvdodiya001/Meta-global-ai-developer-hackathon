"""T1.5 tests (written first): diff by key+hash; in_force before/after commencement."""

from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.core.errors import SourceUnavailable
from app.db import init_db
from app.services import diff, sources

RAW_DIR = Path(__file__).resolve().parents[2] / "corpus" / "raw"

OLD_ID = "SV-DPDP-ACT-V1"
NEW_ID = "SV-DPDP-ACT-V2SIM"


def make_session(tmp_path: Path) -> Session:
    """Open a fresh T1.1 database with the T1.2 corpus loaded (T1.5)."""
    engine = init_db(tmp_path / "diff.db")
    session: Session = sessionmaker(bind=engine, future=True)()
    sources.load_corpus(session, RAW_DIR)
    return session


def by_key(session: Session, version_id: str) -> dict[str, models.Provision]:
    """Index one version's provisions by key (T1.5)."""
    return {row.key: row for row in sources.list_provisions(session, version_id)}


def test_diff_v1_to_v2_flags_changed_key(tmp_path: Path) -> None:
    """T1.5: Done when the v1→v2 diff test passes (key + hash)."""
    session = make_session(tmp_path)
    try:
        result = diff.diff_versions(session, OLD_ID, NEW_ID)
        assert result.changed_keys == ["DPDP-Act-2023_s8(6)"]
        assert result.added_keys == []
        assert result.removed_keys == []
        assert sorted(result.unchanged_keys) == sorted(
            set(by_key(session, OLD_ID)) - {"DPDP-Act-2023_s8(6)"}
        )
        old_rows, new_rows = by_key(session, OLD_ID), by_key(session, NEW_ID)
        assert (
            old_rows["DPDP-Act-2023_s8(6)"].text_sha256
            != new_rows["DPDP-Act-2023_s8(6)"].text_sha256
        )
        assert "SIMULATED AMENDMENT" in new_rows["DPDP-Act-2023_s8(6)"].text
    finally:
        session.close()


def test_diff_identical_version_is_empty(tmp_path: Path) -> None:
    """T1.5: diffing a version against itself finds nothing."""
    session = make_session(tmp_path)
    try:
        result = diff.diff_versions(session, OLD_ID, OLD_ID)
        assert result.changed_keys == []
        assert result.added_keys == []
        assert result.removed_keys == []
        assert len(result.unchanged_keys) == 5
    finally:
        session.close()


def test_diff_unknown_version_raises(tmp_path: Path) -> None:
    """T1.5: diffing a missing version raises a typed error."""
    session = make_session(tmp_path)
    try:
        with pytest.raises(SourceUnavailable):
            diff.diff_versions(session, OLD_ID, "SV-NOPE")
    finally:
        session.close()


def test_in_force_before_commencement(tmp_path: Path) -> None:
    """T1.5: Done when the before-commencement in_force test passes."""
    session = make_session(tmp_path)
    try:
        rows = by_key(session, OLD_ID)
        assert diff.in_force(rows["DPDP-Act-2023_s8(6)"], "2025-10-01") is False
        assert diff.in_force(rows["DPDP-Act-2023_s1"], "2025-11-12") is False
    finally:
        session.close()


def test_in_force_after_commencement(tmp_path: Path) -> None:
    """T1.5: Done when the after-commencement in_force test passes."""
    session = make_session(tmp_path)
    try:
        rows = by_key(session, OLD_ID)
        assert diff.in_force(rows["DPDP-Act-2023_s8(6)"], "2027-05-13") is True
        assert diff.in_force(rows["DPDP-Act-2023_s8(6)"], "2027-05-14") is True
        assert diff.in_force(rows["DPDP-Act-2023_s1"], "2025-11-13") is True
        decoy = by_key(session, "SV-DECOY-V1")["DECOY_Emblems-Act-1950_s3"]
        assert diff.in_force(decoy, "2000-01-01") is True
    finally:
        session.close()


def test_in_force_effective_until() -> None:
    """T1.5: a provision lapses on its effective_until date."""
    row = models.Provision(
        id="PRV-X",
        source_version_id="SV-X",
        key="K",
        text="t",
        text_sha256="s",
        effective_from="2025-01-01",
        effective_until="2026-01-01",
    )
    assert diff.in_force(row, "2025-06-01") is True
    assert diff.in_force(row, "2026-01-01") is False
    assert diff.in_force(row, "2026-06-01") is False
