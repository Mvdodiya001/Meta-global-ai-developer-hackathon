"""T1.3 tests (written first): cards load, spans verify, bad spans rejected."""

import shutil
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.core.errors import RuleCardError
from app.db import init_db
from app.services import rulecards, sources

RAW_DIR = Path(__file__).resolve().parents[2] / "corpus" / "raw"
CARDS_DIR = Path(__file__).resolve().parents[2] / "corpus" / "rulecards"


def make_session(tmp_path: Path) -> Session:
    """Open a fresh T1.1 database with a session (T1.3)."""
    engine = init_db(tmp_path / "cards.db")
    return sessionmaker(bind=engine, future=True)()


def load_all(session: Session) -> list[str]:
    """Ingest the T1.2 corpus then the T1.3 cards (T1.3)."""
    sources.load_corpus(session, RAW_DIR)
    return rulecards.load_rulecards(session, CARDS_DIR)


def test_all_cards_load_and_verify(tmp_path: Path) -> None:
    """T1.3: Done when all cards load and every span verifies."""
    session = make_session(tmp_path)
    ids = load_all(session)
    assert 6 <= len(ids) <= 8
    rows = session.execute(sa.select(models.RuleCard)).scalars().all()
    assert len(rows) == len(ids)
    for row in rows:
        provision = session.get(models.Provision, row.provision_id)
        assert provision is not None
        assert provision.text[row.span_start : row.span_end] == _span_text(row.id)
    session.close()


def _span_text(card_id: str) -> str:
    """Read back the authored span text for one card (T1.3)."""
    cards = rulecards.load_cards(CARDS_DIR)
    return str([card for card in cards if card["id"] == card_id][0]["span_text"])


def test_claim_types_covered(tmp_path: Path) -> None:
    """T1.3: Done when the cards cover CT1–CT3."""
    session = make_session(tmp_path)
    load_all(session)
    types = {
        row.claim_type
        for row in session.execute(sa.select(models.RuleCard)).scalars().all()
    }
    assert {"CT1", "CT2", "CT3"} <= types
    session.close()


def test_span_not_in_snapshot_rejected(tmp_path: Path) -> None:
    """T1.3: a card whose span is not in the snapshot is rejected, with no writes."""
    session = make_session(tmp_path)
    sources.load_corpus(session, RAW_DIR)
    bad_dir = tmp_path / "rulecards"
    shutil.copytree(CARDS_DIR, bad_dir)
    first = sorted(bad_dir.glob("*.yaml"))[0]
    text = first.read_text(encoding="utf-8")
    first.write_text(
        text.replace(
            "reasonable security safeguards; and",
            "reasonable security safeguards!!!",
        ),
        encoding="utf-8",
    )
    with pytest.raises(RuleCardError):
        rulecards.load_rulecards(session, bad_dir)
    count = session.execute(sa.select(sa.func.count()).select_from(models.RuleCard))
    assert count.scalar() == 0
    session.close()


def test_unknown_provision_rejected(tmp_path: Path) -> None:
    """T1.3: a card citing a missing provision is rejected."""
    session = make_session(tmp_path)
    sources.load_corpus(session, RAW_DIR)
    bad_dir = tmp_path / "rulecards"
    shutil.copytree(CARDS_DIR, bad_dir)
    first = sorted(bad_dir.glob("*.yaml"))[0]
    text = first.read_text(encoding="utf-8")
    first.write_text(
        text.replace("PRV-DPDP-", "PRV-NOPE-"), encoding="utf-8"
    )
    with pytest.raises(RuleCardError):
        rulecards.load_rulecards(session, bad_dir)
    session.close()


def test_malformed_card_rejected(tmp_path: Path) -> None:
    """T1.3: a card with an unknown key is rejected."""
    session = make_session(tmp_path)
    sources.load_corpus(session, RAW_DIR)
    bad_dir = tmp_path / "rulecards"
    shutil.copytree(CARDS_DIR, bad_dir)
    (bad_dir / "RC-BAD.yaml").write_text(
        "id: RC-BAD\nprovision_id: PRV-X\nbogus_key: 1\n", encoding="utf-8"
    )
    with pytest.raises(RuleCardError):
        rulecards.load_rulecards(session, bad_dir)
    session.close()


def test_ingest_is_idempotent(tmp_path: Path) -> None:
    """T1.3: loading twice keeps one row per card."""
    session = make_session(tmp_path)
    first = load_all(session)
    second = load_all(session)
    assert first == second
    count = session.execute(sa.select(sa.func.count()).select_from(models.RuleCard))
    assert count.scalar() == len(first)
    session.close()
