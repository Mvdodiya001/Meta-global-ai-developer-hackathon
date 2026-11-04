"""P1-hybrid: FalkorDB-first traversal with relational fallback.

Fallback tests run everywhere (closed port refuses instantly). The live
test tries the configured FalkorDB and skips when unreachable, so CI
never depends on a graph server.
"""

from pathlib import Path

import pytest
from sqlalchemy.orm import sessionmaker

from app.db import init_db
from app.modules.evidence import graph, graph_projection
from app.services import seed

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"


def _seeded(tmp_path: Path):
    db = tmp_path / "live.db"
    seed.seed_demo(db, CORPUS_ROOT)
    session = sessionmaker(bind=init_db(db), future=True)()
    return session


def test_live_falls_back_without_graph_server(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Closed port: backend reports relational and ids match the CTE."""
    monkeypatch.setenv("CT_GRAPH_HOST", "127.0.0.1")
    monkeypatch.setenv("CT_GRAPH_PORT", "1")
    session = _seeded(tmp_path)
    try:
        assert graph.graph_backend(session) == "relational"
        live, backend = graph.dependent_findings_live(
            session, "PRV-DPDP-Act-2023-s8-6"
        )
        assert backend == "relational"
        assert live == graph.dependent_findings(session, "PRV-DPDP-Act-2023-s8-6")
        assert "FND-RC-CT3-BREACH-01" in live
    finally:
        session.close()


def test_live_applies_current_filter_on_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Projection ids are CURRENT-filtered on the record side."""
    session = _seeded(tmp_path)
    recorded = graph.dependent_findings(session, "PRV-DPDP-Act-2023-s8-6")
    assert recorded, "seed must have a CURRENT dependent for s8-6"

    def fake_ensure(sess):
        return "test-graph"

    def fake_query(name, provision_id):
        assert provision_id == "PRV-DPDP-Act-2023-s8-6"
        return [*recorded, "FND-DOES-NOT-EXIST"]

    monkeypatch.setattr(graph_projection, "ensure_projected", fake_ensure)
    monkeypatch.setattr(graph_projection, "dependent_findings", fake_query)
    try:
        live, backend = graph.dependent_findings_live(
            session, "PRV-DPDP-Act-2023-s8-6"
        )
        assert backend == "falkordb"
        assert live == recorded
    finally:
        session.close()


def test_live_against_real_falkordb_when_reachable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end hybrid path on a live server; skips when unreachable."""
    monkeypatch.setenv("CT_GRAPH_NAME", "clausetrace-hybrid-test")
    session = _seeded(tmp_path)
    try:
        try:
            name = graph_projection.ensure_projected(session)
        except Exception:
            pytest.skip("no reachable FalkorDB; fallback covered above")
            return
        assert name == "clausetrace-hybrid-test"
        assert graph.graph_backend(session) == "falkordb"
        live, backend = graph.dependent_findings_live(
            session, "PRV-DPDP-Act-2023-s8-6"
        )
        assert backend == "falkordb"
        assert live == graph.dependent_findings(session, "PRV-DPDP-Act-2023-s8-6")
        assert "FND-RC-CT3-BREACH-01" in live
    finally:
        session.close()
