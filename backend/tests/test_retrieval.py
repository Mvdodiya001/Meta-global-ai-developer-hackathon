"""Phase 3: deterministic provision retrieval across all current sources."""

from pathlib import Path

import pytest
from sqlalchemy.orm import sessionmaker

from app.db import init_db
from app.modules.evidence import retrieval
from app.services import sources

RAW_DIR = Path(__file__).resolve().parents[2] / "corpus" / "raw"


@pytest.fixture()
def session(tmp_path: Path):
    engine = init_db(tmp_path / "retrieval.db")
    sess = sessionmaker(bind=engine, future=True)()
    sources.load_corpus(sess, RAW_DIR)
    yield sess
    sess.close()


def keys(hits: list[dict]) -> list[str]:
    return [hit["key"] for hit in hits]


def test_breach_question_finds_breach_section(session) -> None:
    """Phase 3: breach intimation ranks DPDP s8(6) first."""
    hits = retrieval.search_provisions(
        session, "personal data breach intimation to the Board and each affected Data Principal"
    )
    assert hits, "expected hits"
    assert hits[0]["key"] == "DPDP-Act-2023_s8(6)"


def test_consent_question_finds_consent_section(session) -> None:
    """Phase 3: consent withdrawal ranks DPDP s6 in the top hits."""
    hits = retrieval.search_provisions(
        session, "consent free specific informed withdraw consent at any time"
    )
    assert "DPDP-Act-2023_s6" in keys(hits)[:3]


def test_transfer_question_finds_outside_india_section(session) -> None:
    """Phase 3: cross-border transfer ranks DPDP s16 in the top hits."""
    hits = retrieval.search_provisions(
        session, "transfer of personal data outside India to another country"
    )
    assert "DPDP-Act-2023_s16" in keys(hits)[:3]


def test_copyright_question_reaches_copyright_act(session) -> None:
    """Phase 3: assignment questions reach the Copyright Act, not only DPDP."""
    hits = retrieval.search_provisions(
        session, "assignment of copyright owner assignee rights duration territorial extent"
    )
    assert any(hit["source_id"] == "SRC-COPYRIGHT-ACT" for hit in hits[:3])


def test_intermediary_question_reaches_it_act(session) -> None:
    """Phase 3: intermediary safe harbour ranks IT Act s79 in the top hits."""
    hits = retrieval.search_provisions(
        session, "intermediary not liable third party information hosted safe harbour"
    )
    assert "IT-Act-2000_s79" in keys(hits)[:3]


def test_semantic_abroad_reaches_outside_india(session) -> None:
    """Phase 3 semantic: 'abroad' (not in the Act) still reaches s16."""
    hits = retrieval.search_provisions(session, "sending personal data abroad for processing")
    assert "DPDP-Act-2023_s16" in keys(hits)[:3]


def test_semantic_leak_reaches_breach_section(session) -> None:
    """Phase 3 semantic: 'data leak' reaches the breach intimation section."""
    hits = retrieval.search_provisions(session, "notify the board after a data leak")
    assert "DPDP-Act-2023_s8(6)" in keys(hits)[:3]


def test_simulated_version_never_ranked(session) -> None:
    """Phase 3: the simulated amendment is excluded from retrieval."""
    hits = retrieval.search_provisions(session, "breach intimation forty-eight hours")
    assert all(hit["source_version_id"] != "SV-DPDP-ACT-V2SIM" for hit in hits)
