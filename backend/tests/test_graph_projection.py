"""Rewrite P1: FalkorDB projection parity with the record traversal."""

import os
from pathlib import Path

import pytest
from sqlalchemy.orm import sessionmaker

from app.db import init_db
from app.modules.evidence import graph_projection
from app.services import graph, seed

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"

pytestmark = pytest.mark.skipif(
    not os.environ.get("CT_GRAPH_TEST"),
    reason="set CT_GRAPH_TEST=1 with a reachable FalkorDB to run parity",
)


def test_projection_matches_record_traversal(tmp_path: Path) -> None:
    """P1: projected graph returns the same dependents as Postgres/SQLite."""
    db = tmp_path / "proj.db"
    seed.seed_demo(db, CORPUS_ROOT)
    session = sessionmaker(bind=init_db(db), future=True)()
    counts = graph_projection.project(session, "clausetrace-test")
    assert counts["nodes"] > 0 and counts["edges"] > 0
    for provision_id in (
        "PRV-DPDP-Act-2023-s8-6",
        "PRV-DECOY-Emblems-Act-1950-s3",
    ):
        projected = graph_projection.dependent_findings("clausetrace-test", provision_id)
        recorded = graph.dependent_findings(session, provision_id)
        # Projection is the raw traversal; record side filters CURRENT.
        assert set(recorded) <= set(projected)
        if provision_id.endswith("s8-6"):
            assert "FND-RC-CT3-BREACH-01" in projected
        else:
            assert projected == []
    session.close()
