"""T4.5 tests: real endpoints against scratch databases (contract v1)."""

import asyncio
import hashlib
from pathlib import Path
from typing import Any

import httpx
import pytest
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.agent import claims
from app.agent.loop import LoopResult
from app.db import init_db
from app.services import graph, seed

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"


def seed_compact(db_path: str) -> None:
    """Small wired database: doc chain, versions, card, fact, finding (T4.5)."""
    engine = init_db(db_path)
    session = sessionmaker(bind=engine, future=True)()
    session.add(models.Matter(id="MAT-01", client_name="Acme", title="M1"))
    session.add(models.Document(id="DOC-01", matter_id="MAT-01", title="DPA", kind="dpa"))
    session.add(
        models.DocumentVersion(
            id="DV-01",
            document_id="DOC-01",
            text="contract text",
            sha256="0" * 64,
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Clause(
            id="CL-01",
            document_version_id="DV-01",
            ref="9.2",
            heading="Transfer",
            text="transfer logs",
            span_start=0,
            span_end=5,
        )
    )
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
    for vid, sup in (("SV-01", None), ("SV-02", "SV-01")):
        session.add(
            models.SourceVersion(
                id=vid,
                source_id="SRC-01",
                version_label=vid,
                published_on="2023-08-11",
                effective_from="2023-08-11",
                effective_until=None,
                retrieved_at="2026-01-01T00:00:00Z",
                content_sha256="0" * 64,
                raw_text="text",
                is_simulated=False,
                supersedes_id=sup,
            )
        )
    for pid, vid, key, text in (
        ("PRV-01", "SV-01", "Section 6", "s6 v1"),
        ("PRV-02", "SV-01", "Section 7", "s7"),
        ("PRV-03", "SV-02", "Section 6", "s6 v2"),
        ("PRV-04", "SV-02", "Section 7", "s7"),
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
    session.add(
        models.RuleCard(
            id="RC-01",
            provision_id="PRV-01",
            kind="statutory",
            claim_type="CT2",
            predicate_json=None,
            interpretation_text="interp",
            span_start=0,
            span_end=2,
            trust_class="lawyer_confirmed",
            approved_by="human",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Fact(
            id="F-01",
            matter_id="MAT-01",
            clause_id="CL-01",
            statement="Clause 9.2 requires transfer logs.",
            structured_json={"element": "transfer logs"},
            origin="extracted",
            trust_class="document_extracted",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Claim(
            id="C-01",
            matter_id="MAT-01",
            clause_id="CL-01",
            claim_type="CT2",
            params_json={"element": "transfer logs"},
            question_text="Does clause 9.2 require transfer logs?",
            as_of="2026-11-20",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Run(
            id="RUN-01", trigger="verify", claim_id="C-01", started_at="2026-01-01T00:00:00Z"
        )
    )
    session.add(
        models.Finding(
            id="FND-01",
            claim_id="C-01",
            version_no=1,
            status="FOLLOWS",
            confidence_band="medium",
            proof_json={
                "claim_id": "C-01",
                "as_of": "2026-11-20",
                "conclusion": "holds",
                "premises": [
                    {
                        "fact_id": "F-01",
                        "statement": "Clause 9.2 requires transfer logs.",
                        "trust_class": "document_extracted",
                    }
                ],
                "steps": [
                    {"kind": "cite_fact", "fact_id": "F-01"},
                    {"kind": "conclude", "conclusion": "holds"},
                ],
            },
            as_of="2026-11-20",
            source_version_ids_json=[],
            premise_ids_json=["F-01"],
            rule_card_ids_json=[],
            checker_report_json={"valid": True, "errors": [], "cited_source_versions": []},
            run_id="RUN-01",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.FindingEvent(
            id="FE-01", finding_id="FND-01", state="CURRENT", created_at="2026-01-01T00:00:00Z"
        )
    )
    edges = (
        ("finding", "FND-01", "fact", "F-01", "DEPENDS_ON"),
        ("finding", "FND-01", "rule_card", "RC-01", "DEPENDS_ON"),
        ("rule_card", "RC-01", "provision", "PRV-01", "DERIVED_FROM"),
    )
    for src_type, src_id, dst_type, dst_id, rel in edges:
        graph.add_edge(
            session,
            src_type=src_type,
            src_id=src_id,
            dst_type=dst_type,
            dst_id=dst_id,
            rel=rel,
        )
    session.commit()
    session.close()


def real_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, seed_fn: Any) -> Any:
    """Build the real router app against a scratch database (T4.5)."""
    db_path = str(tmp_path / "api.db")
    monkeypatch.setenv("API_STUB", "0")
    monkeypatch.setenv("CLAUSETRACE_DB", db_path)
    seed_fn(db_path)
    from app.main import create_app

    return create_app()


async def _request(app: Any, method: str, path: str, body: Any = None) -> httpx.Response:
    """In-process ASGI request (T4.5)."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        if method == "get":
            return await client.get(path)
        return await client.post(path, json=body)


def get(app: Any, path: str) -> httpx.Response:
    """Synchronous GET wrapper (T4.5)."""
    return asyncio.run(_request(app, "get", path))


def post(app: Any, path: str, body: Any = None) -> httpx.Response:
    """Synchronous POST wrapper (T4.5)."""
    return asyncio.run(_request(app, "post", path, body))


def test_matter_documents_clauses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """T4.5: matter, documents and clauses read from the database."""
    app = real_app(tmp_path, monkeypatch, seed_compact)
    matter = get(app, "/api/matters/MAT-01")
    assert matter.status_code == 200
    assert matter.json()["client_name"] == "Acme"
    docs = get(app, "/api/matters/MAT-01/documents")
    assert [doc["id"] for doc in docs.json()["documents"]] == ["DOC-01"]
    clauses = get(app, "/api/documents/DOC-01/clauses")
    assert [clause["ref"] for clause in clauses.json()["clauses"]] == ["9.2"]
    assert get(app, "/api/matters/NOPE").status_code == 404
    assert get(app, "/api/documents/NOPE/clauses").status_code == 404


def test_facts_and_trust_actions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """T4.5: facts list plus approve/challenge with validation."""
    app = real_app(tmp_path, monkeypatch, seed_compact)
    facts = get(app, "/api/matters/MAT-01/facts")
    assert [(fact["id"], fact["trust_class"]) for fact in facts.json()["facts"]] == [
        ("F-01", "document_extracted")
    ]
    approved = post(app, "/api/facts/F-01/approve", {"reviewer": "lawyer"})
    assert approved.status_code == 200
    assert approved.json()["trust_class"] == "lawyer_confirmed"
    assert approved.json()["supersedes_id"] == "F-01"
    assert approved.json()["fact_id"] != "F-01"
    bad = post(app, "/api/facts/F-01/challenge", {"reason": ""})
    assert bad.status_code == 400
    assert post(app, "/api/facts/NOPE/approve", {}).status_code == 404


def canned_loop(
    session: Session, **kwargs: Any
) -> LoopResult:
    """A loop that drafts nothing (T4.5 ask-flow)."""
    _ = (session, kwargs)
    return LoopResult(
        run_id="RUN-LOOP",
        accepted=False,
        proof=None,
        report=None,
        outcome="no_proof",
        tool_calls=0,
    )


def test_create_claim_replay(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """T4.5: a recorded question structures into a stored claim plus run."""
    app = real_app(tmp_path, monkeypatch, seed_compact)
    monkeypatch.setattr("app.api.loop_agent.run_verify", canned_loop)
    question = claims.CLAIM_SAMPLES[0]["question"]
    created = post(
        app,
        "/api/claims",
        {"clause_id": "CL-01", "question": question, "as_of": "2026-11-20"},
    )
    assert created.status_code == 200, created.text
    assert created.json()["finding_id"] is None
    # The response carries the loop's run id (canned as RUN-LOOP here),
    # not the claim-open placeholder, so the UI poll finds the trace.
    assert created.json()["run_id"] == "RUN-LOOP"
    assert get(app, "/api/runs/NOPE").status_code == 404
    assert post(app, "/api/claims", {"clause_id": "NOPE", "question": question}).status_code in (
        400,
        422,
    )


def test_demo_question_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ask-flow: the demo question replays to a stored FOLLOWS finding."""
    app = real_app(tmp_path, monkeypatch, lambda db: seed.seed_demo(db, CORPUS_ROOT))
    created = post(
        app,
        "/api/claims",
        {
            "clause_id": "CL-10",
            "question": seed.DEMO_92_QUESTION,
            "as_of": seed.DEMO_92_AS_OF,
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["finding_id"] is not None
    assert body["status"] == "FOLLOWS"
    current = get(app, f"/api/claims/{body['claim_id']}/current")
    assert current.json()["id"] == body["finding_id"]
    assert current.json()["status"] == "FOLLOWS"
    # The returned run is the loop's run: the UI polls it for the trace.
    run = get(app, f"/api/runs/{body['run_id']}")
    assert run.json()["status"] != "running"
    events = get(app, f"/api/runs/{body['run_id']}/events")
    assert len(events.json()["events"]) >= 3


def test_g4_ask_replays_on_seeded_facts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """G4: POST /api/claims replays over HTTP on a freshly seeded DB.

    Regression for the replay-hash 502: the server's loop request must match
    a recorded cassette byte for byte on seed state (seed now carries the
    DOC-01 extraction facts, so the recorded turns embed them).
    """
    app = real_app(tmp_path, monkeypatch, lambda db: seed.seed_demo(db, CORPUS_ROOT))
    created = post(
        app,
        "/api/claims",
        {
            "clause_id": "CL-10",
            "question": seed.DEMO_92_QUESTION,
            "as_of": seed.DEMO_92_AS_OF,
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["finding_id"] is not None
    assert body["status"] == "FOLLOWS"
    current = get(app, f"/api/claims/{body['claim_id']}/current")
    assert current.json()["id"] == body["finding_id"]


def test_user_date_question_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ask-frontend: the 2025-10-17 ask replays to a stored FOLLOWS finding."""
    app = real_app(tmp_path, monkeypatch, lambda db: seed.seed_demo(db, CORPUS_ROOT))
    created = post(
        app,
        "/api/claims",
        {
            "clause_id": "CL-10",
            "question": seed.DEMO_92_QUESTION,
            "as_of": "2025-10-17",
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["finding_id"] is not None
    assert body["status"] == "FOLLOWS"
    current = get(app, f"/api/claims/{body['claim_id']}/current")
    assert current.json()["id"] == body["finding_id"]
    assert current.json()["status"] == "FOLLOWS"


def test_demo_question_with_mismatched_clause_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ask-502: question naming clause 9.2 wins over a stale clause_id.

    Regression: the UI sent clause_id CL-03 (clause 3 selected) with the
    default 9.2 question. The loop prompt embeds the target clause text, so
    the replay hash missed every cassette and the endpoint returned 502.
    The claim must be stored against clause 9.2 (CL-10), not clause 3.
    """
    app = real_app(tmp_path, monkeypatch, lambda db: seed.seed_demo(db, CORPUS_ROOT))
    created = post(
        app,
        "/api/claims",
        {
            "clause_id": "CL-03",
            "question": seed.DEMO_92_QUESTION,
            "as_of": seed.DEMO_92_AS_OF,
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["finding_id"] is not None
    assert body["status"] == "FOLLOWS"
    current = get(app, f"/api/claims/{body['claim_id']}/current")
    assert current.json()["status"] == "FOLLOWS"
    engine = init_db(str(tmp_path / "api.db"))
    session = sessionmaker(bind=engine, future=True)()
    claim = session.get(models.Claim, body["claim_id"])
    assert claim is not None
    assert claim.clause_id == "CL-10"
    session.close()


def test_unknown_question_returns_unknown_finding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Gate: an UNKNOWN-typed question decides UNKNOWN, never a 502.

    Regression: create_claim ran the agent loop for UNKNOWN claims; the
    loop has no recorded proof path for them, so replay raised 502 and no
    finding was stored. The memory service decides UNKNOWN directly.
    """
    app = real_app(tmp_path, monkeypatch, lambda db: seed.seed_demo(db, CORPUS_ROOT))
    created = post(
        app,
        "/api/claims",
        {
            "clause_id": "CL-10",
            "question": "Is this agreement fair to Nimbus?",
            "as_of": seed.DEMO_92_AS_OF,
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["status"] == "UNKNOWN"
    assert body["finding_id"] is not None
    current = get(app, f"/api/claims/{body['claim_id']}/current")
    assert current.json()["status"] == "UNKNOWN"
    assert current.json()["checker_report"] is None


def test_challenger_miss_still_decides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Gate: CHALLENGER=on with no recorded review must not 502 the ask.

    Regression: the 2025-10-17 proof has no challenger cassette, so the
    second pass raised CassetteMissing inside decide_finding and the
    whole POST /api/claims returned 502 with no finding stored. An
    unavailable challenger forces REQUIRES_REVIEW instead.
    """
    monkeypatch.setenv("CHALLENGER", "on")
    app = real_app(tmp_path, monkeypatch, lambda db: seed.seed_demo(db, CORPUS_ROOT))
    created = post(
        app,
        "/api/claims",
        {
            "clause_id": "CL-10",
            "question": seed.DEMO_92_QUESTION,
            "as_of": "2025-10-17",
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["finding_id"] is not None
    assert body["status"] == "REQUIRES_REVIEW"
    current = get(app, f"/api/claims/{body['claim_id']}/current")
    assert current.json()["challenger_report"] is None


def test_proof_round_trip_verifies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Gate: a proof read back from the API verifies as-is; tamper fails.

    Regression: ProofStep dropped checker fields (clause_id, quote) and
    emitted null keys, so the untampered proof from GET current failed
    /api/proofs/verify with CITATION_MALFORMED — the Screen 3 tamper demo
    could not distinguish tampered from untampered.
    """
    app = real_app(tmp_path, monkeypatch, lambda db: seed.seed_demo(db, CORPUS_ROOT))
    created = post(
        app,
        "/api/claims",
        {
            "clause_id": "CL-10",
            "question": seed.DEMO_92_QUESTION,
            "as_of": seed.DEMO_92_AS_OF,
        },
    )
    assert created.status_code == 200, created.text
    claim_id = created.json()["claim_id"]
    proof = get(app, f"/api/claims/{claim_id}/current").json()["proof"]
    steps = {step["kind"]: step for step in proof["steps"]}
    assert steps["contains_element"]["clause_id"] == "CL-10"
    assert steps["contains_element"]["quote"]
    good = post(app, "/api/proofs/verify", {"claim_id": claim_id, "proof": proof})
    assert good.status_code == 200, good.text
    assert good.json()["valid"] is True, good.text
    proof["premises"][0]["statement"] = "TAMPERED STATEMENT"
    bad = post(app, "/api/proofs/verify", {"claim_id": claim_id, "proof": proof})
    assert bad.json()["valid"] is False
    codes = [error["code"] for error in bad.json()["errors"]]
    assert "PREMISE_MISMATCH" in codes


def test_challenger_report_returned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ask-frontend: CHALLENGER=on stores the review and the payload echoes it."""
    monkeypatch.setenv("CHALLENGER", "on")
    app = real_app(tmp_path, monkeypatch, lambda db: seed.seed_demo(db, CORPUS_ROOT))
    created = post(
        app,
        "/api/claims",
        {
            "clause_id": "CL-10",
            "question": seed.DEMO_92_QUESTION,
            "as_of": seed.DEMO_92_AS_OF,
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["finding_id"] is not None
    current = get(app, f"/api/claims/{body['claim_id']}/current")
    report = current.json()["challenger_report"]
    assert report is not None
    assert report["model"] == "muse-spark-1.2"
    assert isinstance(report["blocking"], bool)
    assert isinstance(report["objections"], list)
    if report["blocking"]:
        assert current.json()["status"] == "REQUIRES_REVIEW"
    else:
        assert current.json()["status"] == "FOLLOWS"


def test_current_history_review(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """T4.5: current/history/review round-trip on a stored finding."""
    app = real_app(tmp_path, monkeypatch, seed_compact)
    current = get(app, "/api/claims/C-01/current")
    assert current.status_code == 200
    assert current.json()["status"] == "FOLLOWS"
    assert current.json()["state"] == "CURRENT"
    assert "not yet reviewed" in current.json()["ai_draft_label"]
    history = get(app, "/api/claims/C-01/history")
    assert [finding["version_no"] for finding in history.json()["versions"]] == [1]
    assert get(app, "/api/findings/FND-01").json()["id"] == "FND-01"
    reviewed = post(app, "/api/findings/FND-01/review", {"action": "approve", "note": "ok"})
    assert reviewed.status_code == 200
    assert reviewed.json() == {"finding_id": "FND-01", "state": "REVIEWED"}
    assert "Reviewed by lawyer" in get(app, "/api/findings/FND-01").json()["ai_draft_label"]
    assert post(app, "/api/findings/FND-01/review", {"action": "bogus"}).status_code == 400
    assert get(app, "/api/findings/NOPE").status_code == 404
    assert get(app, "/api/claims/NOPE/current").status_code == 404


def test_sources_versions_diff(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """T4.5: registry reads plus a two-version diff."""
    app = real_app(tmp_path, monkeypatch, seed_compact)
    assert [source["id"] for source in get(app, "/api/sources").json()["sources"]] == ["SRC-01"]
    versions = get(app, "/api/sources/SRC-01/versions").json()["versions"]
    assert [version["id"] for version in versions] == ["SV-01", "SV-02"]
    diff = get(app, "/api/source-versions/SV-02/diff?against=SV-01").json()
    assert diff["changed_keys"] == ["Section 6"]
    assert len(diff["before"]) == 2
    assert len(diff["after"]) == 2
    assert get(app, "/api/sources/NOPE/versions").status_code == 404


def test_ingest_impact_reverify(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """T4.5: ingest flags FND-01 stale; reverify replaces it."""
    app = real_app(tmp_path, monkeypatch, seed_compact)
    ingested = post(
        app,
        "/api/sources/SRC-01/ingest",
        {
            "version": {
                "version_label": "v3",
                "published_on": "2026-06-01",
                "effective_from": "2026-06-01",
                "provisions": [
                    {"key": "Section 6", "text": "s6 v3", "effective_from": "2026-06-01"},
                    {"key": "Section 7", "text": "s7", "effective_from": "2023-08-11"},
                ],
            }
        },
    )
    assert ingested.status_code == 200, ingested.text
    impact_id = ingested.json()["impact_report_id"]
    report = get(app, f"/api/impact/{impact_id}").json()
    assert report["affected"] == [
        {
            "claim_id": "C-01",
            "finding_id": "FND-01",
            "state": "STALE",
            "status_label": "Needs re-check: the law it relied on has changed",
            "clause_ref": "9.2",
        }
    ]
    reverify = post(app, f"/api/impact/{impact_id}/reverify", {"proofs": {}})
    assert reverify.status_code == 200, reverify.text
    assert reverify.json()["superseded"] == ["FND-01"]
    assert len(reverify.json()["current"]) == 1
    assert get(app, f"/api/impact/{impact_id}").json()["affected"] == []
    assert get(app, "/api/impact/IMP-NOPE").status_code == 404
    assert post(app, "/api/sources/SRC-01/ingest", {"fixture": "x"}).status_code == 400


def test_audit_includes_impact_for_matter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """E2E regression: matter-scoped audit shows impact.applied rows.

    Impact audit details carry stale finding ids, not a matter id; the
    matter filter must resolve them through finding -> claim -> matter,
    otherwise Screen 2's audit panel hides the amendment event.
    """
    app = real_app(tmp_path, monkeypatch, seed_compact)
    ingested = post(
        app,
        "/api/sources/SRC-01/ingest",
        {
            "version": {
                "version_label": "v3",
                "published_on": "2026-06-01",
                "effective_from": "2026-06-01",
                "provisions": [
                    {"key": "Section 6", "text": "s6 v3", "effective_from": "2026-06-01"},
                    {"key": "Section 7", "text": "s7", "effective_from": "2023-08-11"},
                ],
            }
        },
    )
    assert ingested.status_code == 200, ingested.text
    events = [row["event"] for row in get(app, "/api/audit?matter_id=MAT-01").json()["rows"]]
    assert "impact.applied" in events


def test_graph_and_audit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """T4.5: graph slice has the wired nodes; audit records lawyer actions."""
    app = real_app(tmp_path, monkeypatch, seed_compact)
    post(app, "/api/facts/F-01/approve", {"reviewer": "lawyer"})
    graph = get(app, "/api/graph?matter_id=MAT-01").json()
    kinds = {node["id"]: node["kind"] for node in graph["nodes"]}
    assert kinds.get("FND-01") == "finding"
    assert kinds.get("F-01") == "fact"
    assert kinds.get("RC-01") == "rule_card"
    assert kinds.get("PRV-01") == "provision"
    rels = {(edge["src"], edge["dst"], edge["rel"]) for edge in graph["edges"]}
    assert ("FND-01", "F-01", "DEPENDS_ON") in rels
    assert ("RC-01", "PRV-01", "DERIVED_FROM") in rels
    assert ("PRV-01", "SV-01", "PART_OF") in rels
    focused = get(app, "/api/graph?matter_id=MAT-01&focus=FND-01").json()
    assert "FND-01" in {node["id"] for node in focused["nodes"]}
    assert get(app, "/api/graph?matter_id=MAT-01&focus=NOPE").status_code == 404
    assert get(app, "/api/graph").status_code == 400
    audit = get(app, "/api/audit?matter_id=MAT-01").json()["rows"]
    assert [row["event"] for row in audit] == ["fact.approved"]
    assert get(app, "/api/audit").json()["rows"] != []


def test_proofs_verify_and_misc(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """T4.5: tamper demo verdicts, counterfactual honesty, demo guards."""
    app = real_app(tmp_path, monkeypatch, seed_compact)
    proof = {
        "claim_id": "C-01",
        "as_of": "2026-11-20",
        "conclusion": "holds",
        "premises": [
            {
                "fact_id": "F-01",
                "statement": "Clause 9.2 requires transfer logs.",
                "trust_class": "document_extracted",
            }
        ],
        "steps": [
            {"kind": "cite_fact", "fact_id": "F-01"},
            {"kind": "conclude", "conclusion": "holds"},
        ],
    }
    good = post(app, "/api/proofs/verify", {"claim_id": "C-01", "proof": proof})
    assert good.json()["valid"] is True
    bad_proof = dict(proof)
    bad_proof["conclusion"] = "fails"
    bad = post(app, "/api/proofs/verify", {"claim_id": "C-01", "proof": bad_proof})
    assert bad.json()["valid"] is False
    assert post(app, "/api/proofs/verify", {"claim_id": "NOPE", "proof": proof}).status_code == 404
    counter = post(app, "/api/counterfactual", {"provision_key": "Section 6"})
    assert counter.json()["available"] is False
    assert post(app, "/api/demo/reset").status_code == 403


def test_extract_persists_version(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """T4.5: extraction on the demo corpus stores a new version + facts."""
    app = real_app(tmp_path, monkeypatch, lambda db: seed.seed_demo(db, CORPUS_ROOT))
    extracted = post(app, "/api/documents/DOC-01/extract", {})
    assert extracted.status_code == 200, extracted.text
    assert len(extracted.json()["clauses"]) == 12
    assert len(extracted.json()["facts"]) == 12
    assert {fact["trust_class"] for fact in extracted.json()["facts"]} == {"document_extracted"}
    clauses = get(app, "/api/documents/DOC-01/clauses").json()["clauses"]
    assert len(clauses) == 12
    facts = get(app, "/api/matters/MAT-01/facts").json()["facts"]
    # G8: seed already carries 13 facts (F-LOOP-92 + F-SEED-01..12).
    assert len(facts) == 25
    assert "F-LOOP-92" in {fact["id"] for fact in facts}


def test_demo_scenario(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """T4.5: DEMO_MODE scenario seeds plus a stale chain; unknown 404s."""
    monkeypatch.setenv("DEMO_MODE", "1")
    app = real_app(tmp_path, monkeypatch, lambda db: seed.seed_demo(db, CORPUS_ROOT))
    scenario = post(app, "/api/demo/scenario/stale-demo", {})
    assert scenario.status_code == 200, scenario.text
    assert scenario.json()["scenario"] == "stale-demo"
    assert scenario.json()["steps"][0] == "seeded demo database"
    assert post(app, "/api/demo/scenario/nope", {}).status_code == 404


def test_reingest_stored_version_stales_card_dependents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F11: ingesting a version that is already stored still marks dependents stale."""
    monkeypatch.setenv("CHALLENGER", "off")
    monkeypatch.setenv("LLM_MODE", "replay")
    app = real_app(tmp_path, monkeypatch, lambda db: seed.seed_demo(db, CORPUS_ROOT))
    simulated: dict[str, Any] | None = None
    source_id = ""
    for source in get(app, "/api/sources").json()["sources"]:
        versions = get(app, f"/api/sources/{source['id']}/versions").json()["versions"]
        match = next(
            (
                version
                for version in versions
                if version["is_simulated"] and version["supersedes_id"]
            ),
            None,
        )
        if match is not None:
            simulated = match
            source_id = str(source["id"])
            break
    assert simulated is not None
    diff = get(
        app,
        f"/api/source-versions/{simulated['id']}/diff?against={simulated['supersedes_id']}",
    ).json()
    created = post(
        app,
        f"/api/sources/{source_id}/ingest",
        {
            "version": {
                "version_label": simulated["version_label"],
                "published_on": simulated["published_on"],
                "effective_from": simulated["effective_from"],
                "provisions": [
                    {
                        "key": row["key"],
                        "text": row["text"],
                        "effective_from": row["effective_from"],
                        "effective_until": row["effective_until"],
                    }
                    for row in diff["after"]
                ],
            }
        },
    )
    assert created.status_code == 200, created.text
    assert created.json()["source_version_id"] == simulated["id"]
    impact = get(app, f"/api/impact/{created.json()['impact_report_id']}").json()
    assert impact["affected"]
    assert {row["state"] for row in impact["affected"]} == {"STALE"}
    reverified = post(app, f"/api/impact/{impact['id']}/reverify", {"proofs": {}})
    assert reverified.status_code == 200, reverified.text
    assert reverified.json()["current"]
    for finding_id in reverified.json()["current"]:
        finding = get(app, f"/api/findings/{finding_id}")
        assert finding.status_code == 200, finding.text
        assert finding.json()["status"] == "REQUIRES_REVIEW"
