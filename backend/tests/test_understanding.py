"""Phase 1: contract understanding extraction + proposed-fact storage."""

from pathlib import Path

from sqlalchemy.orm import sessionmaker

from app import models
from app.db import init_db
from app.modules.intake import understanding

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"


def test_fallback_extracts_parties_and_obligations() -> None:
    """Phase 1: mock-mode fallback reads the seeded DPA deterministically."""
    text = (CORPUS_ROOT / "contracts" / "master_dpa.md").read_text(encoding="utf-8")
    data = understanding.extract_understanding(text, mode="mock")
    names = [party["name"] for party in data["parties"]]
    assert any("Acme" in name for name in names), names
    assert any("Nimbus" in name for name in names), names
    assert data["obligations"], "shall-sentences become obligations"
    assert all("shall" in row["action"] for row in data["obligations"])


def test_store_understanding_as_proposed_facts(tmp_path: Path) -> None:
    """Phase 1: items land as ai_inferred facts, deduped on re-run."""
    engine = init_db(tmp_path / "understanding.db")
    session = sessionmaker(bind=engine, future=True)()
    session.add(models.Matter(id="MAT-01", client_name="Acme", title="M1"))
    session.commit()
    text = (CORPUS_ROOT / "contracts" / "master_dpa.md").read_text(encoding="utf-8")

    counts = understanding.store_understanding(session, matter_id="MAT-01", text=text, mode="mock")
    assert counts["parties"] == 2
    assert counts["obligations"] > 0

    rows = session.query(models.Fact).all()
    assert rows, "understanding facts stored"
    assert all(row.trust_class == "ai_inferred" for row in rows)
    kinds = {str((row.structured_json or {}).get("kind")) for row in rows}
    assert "parties" in kinds and "obligations" in kinds

    again = understanding.store_understanding(session, matter_id="MAT-01", text=text, mode="mock")
    assert sum(again.values()) == 0, "second run must dedupe"
    session.close()
