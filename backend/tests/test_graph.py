"""T4.1 tests (written first): edge graph + reverse traversal."""

from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.db import init_db
from app.services import graph, rulecards, sources

RAW_DIR = Path(__file__).resolve().parents[2] / "corpus" / "raw"
CARDS_DIR = Path(__file__).resolve().parents[2] / "corpus" / "rulecards"


def make_session(tmp_path: Path) -> Session:
    """Open a fresh database with a session (T4.1)."""
    engine = init_db(tmp_path / "graph.db")
    return sessionmaker(bind=engine, future=True)()


def seed(session: Session) -> None:
    """Provisions, cards, findings and edges for traversal tests (T4.1)."""
    session.add(models.Matter(id="MAT-01", client_name="Acme", title="M1"))
    for source_id in ("SRC-01", "SRC-DECOY"):
        session.add(
            models.Source(
                id=source_id,
                key=source_id.lower(),
                title=source_id,
                publisher="MeitY",
                url="https://example.invalid",
                jurisdiction="IN",
            )
        )
    for vid, sid in (("SV-01", "SRC-01"), ("SV-D1", "SRC-DECOY")):
        session.add(
            models.SourceVersion(
                id=vid,
                source_id=sid,
                version_label="v1",
                published_on="2023-08-11",
                effective_from="2023-08-11",
                effective_until=None,
                retrieved_at="2026-01-01T00:00:00Z",
                content_sha256="0" * 64,
                raw_text="text",
                is_simulated=False,
                supersedes_id=None,
            )
        )
    for pid, vid, key in (
        ("PRV-A", "SV-01", "Section 6"),
        ("PRV-B", "SV-01", "Section 7"),
        ("PRV-X", "SV-01", "Section 8"),
        ("PRV-D", "SV-D1", "Decoy provision"),
    ):
        session.add(
            models.Provision(
                id=pid,
                source_version_id=vid,
                key=key,
                text=f"text of {pid}",
                text_sha256="a" * 64,
                effective_from="2023-08-11",
                effective_until=None,
            )
        )
    for cid, pid in (("RC-A", "PRV-A"), ("RC-B", "PRV-B")):
        session.add(
            models.RuleCard(
                id=cid,
                provision_id=pid,
                kind="statutory",
                claim_type="CT2",
                predicate_json=None,
                interpretation_text="interp",
                span_start=0,
                span_end=4,
                trust_class="lawyer_confirmed",
                approved_by="human",
                created_at="2026-01-01T00:00:00Z",
            )
        )
    for cid in ("C-A", "C-B"):
        session.add(models.Claim(
            id=cid,
            matter_id="MAT-01",
            clause_id="CL-01",
            claim_type="CT2",
            params_json=None,
            question_text="q",
            as_of="2026-11-20",
            created_at="2026-01-01T00:00:00Z",
        ))
    for fid, cid in (
        ("FND-A", "C-A"),
        ("FND-A2", "C-A"),
        ("FND-B", "C-B"),
    ):
        session.add(
            models.Finding(
                id=fid,
                claim_id=cid,
                version_no=1,
                status="FOLLOWS",
                confidence_band="high",
                proof_json=None,
                as_of="2026-11-20",
                created_at="2026-01-01T00:00:00Z",
            )
        )
        session.add(
            models.FindingEvent(
                id=f"FE-{fid}",
                finding_id=fid,
                state="CURRENT",
                created_at="2026-01-01T00:00:00Z",
            )
        )
    session.add(
        models.FindingEvent(
            id="FE-A2-SUP",
            finding_id="FND-A2",
            state="SUPERSEDED",
            reason="replaced",
            created_at="2026-01-02T00:00:00Z",
        )
    )
    for src, dst, rel in (
        ("RC-A", "PRV-A", "DERIVED_FROM"),
        ("RC-B", "PRV-B", "DERIVED_FROM"),
        ("FND-A", "RC-A", "DEPENDS_ON"),
        ("FND-A2", "RC-A", "DEPENDS_ON"),
        ("FND-B", "RC-B", "DEPENDS_ON"),
    ):
        graph.add_edge(
            session,
            src_type="rule_card" if src.startswith("RC") else "finding",
            src_id=src,
            dst_type="provision" if dst.startswith("PRV") else "rule_card",
            dst_id=dst,
            rel=rel,
        )
    session.commit()


def test_changed_provision_returns_only_dependent_findings(tmp_path: Path) -> None:
    """T4.1: Done when a changed provision flags only its dependents."""
    session = make_session(tmp_path)
    seed(session)
    assert graph.dependent_findings(session, "PRV-A") == ["FND-A"]
    assert graph.dependent_findings(session, "PRV-B") == ["FND-B"]
    session.close()


def test_decoy_provision_returns_none(tmp_path: Path) -> None:
    """T4.1: Done when the decoy source flags no findings."""
    session = make_session(tmp_path)
    seed(session)
    assert graph.dependent_findings(session, "PRV-D") == []
    session.close()


def test_unrelated_provision_returns_none(tmp_path: Path) -> None:
    """T4.1: Done when an unrelated provision flags no findings."""
    session = make_session(tmp_path)
    seed(session)
    assert graph.dependent_findings(session, "PRV-X") == []
    session.close()


def test_superseded_finding_excluded(tmp_path: Path) -> None:
    """T4.1: findings with a SUPERSEDED event are not dependents."""
    session = make_session(tmp_path)
    seed(session)
    assert "FND-A2" not in graph.dependent_findings(session, "PRV-A")
    session.close()


def test_add_edge_is_idempotent(tmp_path: Path) -> None:
    """T4.1: adding the same edge twice stores one row."""
    session = make_session(tmp_path)
    seed(session)
    before = session.execute(sa.select(sa.func.count()).select_from(models.Edge))
    first = before.scalar()
    assert first is not None
    graph.add_edge(
        session,
        src_type="finding",
        src_id="FND-A",
        dst_type="rule_card",
        dst_id="RC-A",
        rel="DEPENDS_ON",
    )
    session.commit()
    after = session.execute(sa.select(sa.func.count()).select_from(models.Edge))
    assert after.scalar() == first
    session.close()


def test_card_load_creates_derived_edges(tmp_path: Path) -> None:
    """T4.1: loading cards binds each card to its provision exactly once."""
    session = make_session(tmp_path)
    sources.load_corpus(session, RAW_DIR)
    first = rulecards.load_rulecards(session, CARDS_DIR)
    second = rulecards.load_rulecards(session, CARDS_DIR)
    assert first == second
    for card_id in first:
        card = session.get(models.RuleCard, card_id)
        assert card is not None
        rows = session.execute(
            sa.select(models.Edge).where(
                models.Edge.src_type == "rule_card",
                models.Edge.src_id == card_id,
                models.Edge.dst_type == "provision",
                models.Edge.dst_id == card.provision_id,
                models.Edge.rel == "DERIVED_FROM",
            )
        ).scalars().all()
        assert len(rows) == 1
    session.close()
