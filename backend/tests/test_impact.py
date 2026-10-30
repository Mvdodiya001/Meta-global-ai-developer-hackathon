"""T4.2 tests (written first): amendment diff, AFFECTS, STALE, report."""

import hashlib
import time
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.core.errors import SourceUnavailable
from app.db import init_db
from app.services import graph, impact


def make_session(tmp_path: Path) -> Session:
    """Open a fresh database with a session (T4.2)."""
    engine = init_db(tmp_path / "impact.db")
    return sessionmaker(bind=engine, future=True)()


def seed(session: Session) -> None:
    """Two versions with a changed, an added and a removed provision (T4.2)."""
    session.add(models.Matter(id="MAT-01", client_name="Acme", title="M1"))
    session.add(
        models.Source(
            id="SRC-01",
            key="dpdp-act",
            title="DPDP Act",
            publisher="MeitY",
            url="https://example.invalid",
            jurisdiction="IN",
        )
    )
    session.add(
        models.SourceVersion(
            id="SV-01",
            source_id="SRC-01",
            version_label="v1",
            published_on="2023-08-11",
            effective_from="2023-08-11",
            effective_until=None,
            retrieved_at="2026-01-01T00:00:00Z",
            content_sha256="0" * 64,
            raw_text="v1",
            is_simulated=False,
            supersedes_id=None,
        )
    )
    session.add(
        models.SourceVersion(
            id="SV-02",
            source_id="SRC-01",
            version_label="v2",
            published_on="2026-01-01",
            effective_from="2026-01-01",
            effective_until=None,
            retrieved_at="2026-01-02T00:00:00Z",
            content_sha256="1" * 64,
            raw_text="v2",
            is_simulated=True,
            supersedes_id="SV-01",
        )
    )
    for pid, vid, key, text in (
        ("PRV-A1", "SV-01", "Section 6", "old section 6 text"),
        ("PRV-B1", "SV-01", "Section 7", "same section 7 text"),
        ("PRV-D1", "SV-01", "Section 9", "removed section text"),
        ("PRV-A2", "SV-02", "Section 6", "new section 6 text"),
        ("PRV-B2", "SV-02", "Section 7", "same section 7 text"),
        ("PRV-C2", "SV-02", "Section 8", "added section text"),
    ):
        session.add(
            models.Provision(
                id=pid,
                source_version_id=vid,
                key=key,
                text=text,
                text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                effective_from="2023-08-11",
                effective_until=None,
            )
        )
    for cid, pid in (("RC-A", "PRV-A1"), ("RC-B", "PRV-B1")):
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
    for fid, cid in (("FND-A", "C-A"), ("FND-B", "C-B")):
        session.add(
            models.Claim(
                id=cid,
                matter_id="MAT-01",
                clause_id="CL-01",
                claim_type="CT2",
                params_json=None,
                question_text="q",
                as_of="2026-11-20",
                created_at="2026-01-01T00:00:00Z",
            )
        )
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
    for src, dst, rel in (
        ("RC-A", "PRV-A1", "DERIVED_FROM"),
        ("RC-B", "PRV-B1", "DERIVED_FROM"),
        ("FND-A", "RC-A", "DEPENDS_ON"),
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


def test_diff_provisions_by_key_sha_and_dates() -> None:
    """T4.2: changed/added/removed keys detected, effective-date edits count."""
    old = [
        {"key": "Section 6", "sha": "a", "from": "2023-08-11", "until": None},
        {"key": "Section 7", "sha": "b", "from": "2023-08-11", "until": None},
        {"key": "Section 9", "sha": "c", "from": "2023-08-11", "until": None},
    ]
    new = [
        {"key": "Section 6", "sha": "a2", "from": "2023-08-11", "until": None},
        {"key": "Section 7", "sha": "b", "from": "2024-01-01", "until": None},
        {"key": "Section 8", "sha": "d", "from": "2026-01-01", "until": None},
    ]
    assert impact.diff_provisions(old, new) == {
        "changed": ["Section 6", "Section 7"],
        "added": ["Section 8"],
        "removed": ["Section 9"],
    }


def test_apply_version_flags_exactly_expected_findings(tmp_path: Path) -> None:
    """T4.2: Done when the fixture flags FND-A only (G3)."""
    session = make_session(tmp_path)
    seed(session)
    started = time.monotonic()
    report = impact.apply_version(session, "SV-02")
    elapsed = time.monotonic() - started
    assert elapsed < 2.0
    assert report["old_version_id"] == "SV-01"
    assert report["new_version_id"] == "SV-02"
    assert report["changed"] == ["Section 6"]
    assert report["added"] == ["Section 8"]
    assert report["removed"] == ["Section 9"]
    assert report["affected_rule_cards"] == ["RC-A"]
    assert report["stale_findings"] == ["FND-A"]
    stale = session.execute(
        sa.select(models.FindingEvent).where(
            models.FindingEvent.finding_id == "FND-A",
            models.FindingEvent.state == "STALE",
        )
    ).scalars().all()
    assert len(stale) == 1
    assert stale[0].caused_by_type == "source_version"
    assert stale[0].caused_by_id == "SV-02"
    affects = session.execute(
        sa.select(models.Edge).where(models.Edge.rel == "AFFECTS")
    ).scalars().all()
    assert {(edge.src_id, edge.dst_id) for edge in affects} == {
        ("PRV-A2", "RC-A"),
    }
    assert graph.is_current_finding(session, "FND-B")
    audits = session.execute(
        sa.select(models.AuditLog).where(models.AuditLog.event == "impact.applied")
    ).scalars().all()
    assert len(audits) == 1
    session.close()


def test_reapply_is_idempotent(tmp_path: Path) -> None:
    """T4.2: applying the same version twice adds no duplicate rows."""
    session = make_session(tmp_path)
    seed(session)
    first = impact.apply_version(session, "SV-02")
    second = impact.apply_version(session, "SV-02")
    assert first == second
    stale = session.execute(
        sa.select(sa.func.count())
        .select_from(models.FindingEvent)
        .where(models.FindingEvent.state == "STALE")
    ).scalar()
    assert stale == 1
    affects = session.execute(
        sa.select(sa.func.count())
        .select_from(models.Edge)
        .where(models.Edge.rel == "AFFECTS")
    ).scalar()
    assert affects == 1
    session.close()


def test_first_version_has_no_impact(tmp_path: Path) -> None:
    """T4.2: a version with no predecessor changes nothing."""
    session = make_session(tmp_path)
    seed(session)
    report = impact.apply_version(session, "SV-01")
    assert report["changed"] == []
    assert report["stale_findings"] == []
    session.close()


def test_unknown_version_raises(tmp_path: Path) -> None:
    """T4.2: unknown versions raise a typed error."""
    session = make_session(tmp_path)
    seed(session)
    with pytest.raises(SourceUnavailable):
        impact.apply_version(session, "SV-NOPE")
    session.close()
