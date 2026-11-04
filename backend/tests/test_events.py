"""Rewrite P2: domain events fire between modules."""

from pathlib import Path

import pytest
from sqlalchemy.orm import sessionmaker

from app.core import events
from app.db import init_db
from app.modules.evidence import premises
from app.modules.impact import impact
from app.services import seed

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"


@pytest.fixture(autouse=True)
def _clean_events():
    events.clear()
    yield
    events.clear()


def test_fact_approved_and_impact_applied_events(tmp_path: Path) -> None:
    """P2: premise approval and amendment application publish events."""
    db = tmp_path / "events.db"
    seed.seed_demo(db, CORPUS_ROOT)
    session = sessionmaker(bind=init_db(db), future=True)()
    seen: list[tuple[str, dict]] = []
    events.subscribe("fact.approved", lambda payload: seen.append(("fact.approved", payload)))
    events.subscribe("impact.applied", lambda payload: seen.append(("impact.applied", payload)))

    new = premises.approve_fact(session, fact_id="F-SEED-01", reviewer="lawyer")
    assert seen[0][0] == "fact.approved"
    assert seen[0][1]["supersedes_id"] == "F-SEED-01"
    assert seen[0][1]["fact_id"] == new.id

    impact.apply_version(session, "SV-DPDP-ACT-V2SIM")
    assert seen[1][0] == "impact.applied"
    assert seen[1][1]["source_version_id"] == "SV-DPDP-ACT-V2SIM"
    assert "FND-RC-CT3-BREACH-01" in seen[1][1]["stale_findings"]
    session.close()


def test_failing_handler_propagates() -> None:
    """P2: a failing handler is loud, never silently swallowed."""

    def boom(_payload: dict) -> None:
        raise RuntimeError("handler failed")

    events.subscribe("impact.applied", boom)
    with pytest.raises(RuntimeError, match="handler failed"):
        events.emit("impact.applied", {})
