"""T2.4 tests (written first): six tool schemas, matter scoping, call cap.

Tools are deterministic (DB + checker only); no model calls, no cassettes.
"""

from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.agent import tools
from app.core.errors import SourceUnavailable, ToolError
from app.db import init_db

MATTER = "MAT-01"
OTHER_MATTER = "MAT-02"


def make_session(tmp_path: Path) -> Session:
    """Open a fresh database with a session (T2.4)."""
    engine = init_db(tmp_path / "tools.db")
    return sessionmaker(bind=engine, future=True)()


def seed(session: Session) -> None:
    """Two matters, one source with a superseded + current version (T2.4)."""
    session.add(models.Matter(id=MATTER, client_name="Acme", title="M1"))
    session.add(models.Matter(id=OTHER_MATTER, client_name="Other", title="M2"))
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
                is_simulated=vid == "SV-02",
                supersedes_id=sup,
            )
        )
    session.add(
        models.Provision(
            id="PRV-01",
            source_version_id="SV-01",
            key="Section 6",
            text="old text",
            text_sha256="a" * 64,
            effective_from="2023-08-11",
            effective_until=None,
        )
    )
    for num in range(1, 8):
        session.add(
            models.Provision(
                id=f"PRV-2{num}",
                source_version_id="SV-02",
                key=f"Section {num}",
                text=f"provision {num} text",
                text_sha256="b" * 64,
                effective_from="2026-01-01",
                effective_until=None,
            )
        )
    session.add(
        models.Clause(
            id="CL-01",
            document_version_id="DOCV-01",
            ref="9.2",
            heading="Transfer",
            text="Nimbus may transfer order data outside India.",
            span_start=0,
            span_end=10,
        )
    )
    session.add(
        models.Fact(
            id="F-01",
            matter_id=MATTER,
            clause_id="CL-01",
            statement="Clause 9.2 permits transfer.",
            structured_json={"element": "transfer"},
            origin="extracted",
            trust_class="document_extracted",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Fact(
            id="F-02",
            matter_id=OTHER_MATTER,
            clause_id=None,
            statement="Other matter fact.",
            structured_json=None,
            origin="lawyer",
            trust_class="lawyer_confirmed",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Claim(
            id="C-01",
            matter_id=MATTER,
            clause_id="CL-01",
            claim_type="CT2",
            params_json={"element": "transfer"},
            question_text="Must Nimbus transfer data?",
            as_of="2027-06-01",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Claim(
            id="C-02",
            matter_id=OTHER_MATTER,
            clause_id="CL-01",
            claim_type="CT2",
            params_json=None,
            question_text="Other matter claim?",
            as_of="2027-06-01",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Run(
            id="RUN-01",
            trigger="verify",
            claim_id="C-01",
            started_at="2026-01-01T00:00:00Z",
        )
    )
    session.commit()


def call(
    session: Session, tool_name: str, args: dict[str, Any], run: str = "RUN-01"
) -> dict[str, Any]:
    """Dispatch one tool call in the session matter (T2.4)."""
    return tools.call_tool(
        session, run_id=run, matter_id=MATTER, tool=tool_name, args=args
    )


def tool_rows(session: Session, run: str = "RUN-01") -> list[models.ToolCall]:
    """Logged tool calls for a run in sequence order (T2.4)."""
    return list(
        session.execute(
            sa.select(models.ToolCall)
            .where(models.ToolCall.run_id == run)
            .order_by(models.ToolCall.seq)
        )
        .scalars()
        .all()
    )


def valid_proof() -> dict[str, Any]:
    """A checker-valid draft proof over the seeded fact (T2.4)."""
    return {
        "claim_id": "C-01",
        "as_of": "2027-06-01",
        "conclusion": "holds",
        "premises": [
            {
                "fact_id": "F-01",
                "statement": "Clause 9.2 permits transfer.",
                "trust_class": "document_extracted",
            }
        ],
        "steps": [
            {"kind": "cite_fact", "fact_id": "F-01"},
            {"kind": "conclude", "conclusion": "holds"},
        ],
    }


def test_tool_names_match_contract() -> None:
    """T2.4: exactly the six tools from DATA_MODEL_API §4."""
    assert [schema["name"] for schema in tools.TOOL_SCHEMAS] == [
        "lookup_source",
        "list_dependent_claims",
        "get_premise",
        "verify_derivation",
        "propose_finding",
        "request_lawyer_review",
    ]
    required = {schema["name"]: schema["parameters"]["required"] for schema in tools.TOOL_SCHEMAS}
    assert required["lookup_source"] == ["source_id"]
    assert required["get_premise"] == ["matter_id", "premise_id"]
    assert required["verify_derivation"] == ["claim_id", "proof"]
    assert required["propose_finding"] == ["claim_id", "proof"]
    assert required["request_lawyer_review"] == ["item_type", "item_id", "reason"]


def test_lookup_source_defaults_to_current(tmp_path: Path) -> None:
    """T2.4: `version` omitted resolves to the non-superseded version."""
    session = make_session(tmp_path)
    seed(session)
    result = call(session, "lookup_source", {"source_id": "SRC-01"})
    assert result["source_version_id"] == "SV-02"
    assert result["is_simulated"] is True
    assert len(result["provisions"]) == 5
    assert result["truncated"] is True
    first = result["provisions"][0]
    assert set(first) == {"provision_id", "key", "text", "sha256"}
    session.close()


def test_lookup_source_version_and_key_filter(tmp_path: Path) -> None:
    """T2.4: an explicit version plus provision_key narrows the snapshot."""
    session = make_session(tmp_path)
    seed(session)
    result = call(
        session,
        "lookup_source",
        {"source_id": "SRC-01", "version": "SV-01", "provision_key": "Section 6"},
    )
    assert result["source_version_id"] == "SV-01"
    assert [item["provision_id"] for item in result["provisions"]] == ["PRV-01"]
    assert result["truncated"] is False
    session.close()


def test_lookup_source_unknown_version_raises(tmp_path: Path) -> None:
    """T2.4: unknown sources and versions raise a typed error."""
    session = make_session(tmp_path)
    seed(session)
    with pytest.raises(SourceUnavailable):
        call(session, "lookup_source", {"source_id": "SRC-NOPE"})
    with pytest.raises(SourceUnavailable):
        call(session, "lookup_source", {"source_id": "SRC-01", "version": "SV-NOPE"})
    session.close()


def test_get_premise_returns_trust_and_span(tmp_path: Path) -> None:
    """T2.4: one fact with its trust class and origin span."""
    session = make_session(tmp_path)
    seed(session)
    result = call(
        session, "get_premise", {"matter_id": MATTER, "premise_id": "F-01"}
    )
    assert result["fact_id"] == "F-01"
    assert result["trust_class"] == "document_extracted"
    assert result["origin"] == {"clause_id": "CL-01", "span": [0, 10]}
    session.close()


def test_cross_matter_access_rejected(tmp_path: Path) -> None:
    """T2.4: Done when any arg pointing at another matter is rejected."""
    session = make_session(tmp_path)
    seed(session)
    with pytest.raises(ToolError) as arg_matter:
        call(session, "get_premise", {"matter_id": OTHER_MATTER, "premise_id": "F-01"})
    assert arg_matter.value.code == "cross_matter"
    with pytest.raises(ToolError) as row_matter:
        call(session, "get_premise", {"matter_id": MATTER, "premise_id": "F-02"})
    assert row_matter.value.code == "cross_matter"
    with pytest.raises(ToolError) as claim_matter:
        call(
            session,
            "verify_derivation",
            {"claim_id": "C-02", "proof": valid_proof()},
        )
    assert claim_matter.value.code == "cross_matter"
    session.close()


def test_thirteenth_call_rejected(tmp_path: Path) -> None:
    """T2.4: Done when the 13th call in one run is rejected."""
    session = make_session(tmp_path)
    seed(session)
    for _ in range(12):
        call(session, "lookup_source", {"source_id": "SRC-01"})
    with pytest.raises(ToolError) as budget:
        call(session, "lookup_source", {"source_id": "SRC-01"})
    assert budget.value.code == "tool_budget_exhausted"
    session.close()


def test_unknown_tool_rejected(tmp_path: Path) -> None:
    """T2.4: Done when a tool outside the six is rejected."""
    session = make_session(tmp_path)
    seed(session)
    with pytest.raises(ToolError) as unknown:
        call(session, "browse_web", {})
    assert unknown.value.code == "unknown_tool"
    session.close()


def test_verify_derivation_valid_and_tampered(tmp_path: Path) -> None:
    """T2.4: the checker verdict passes through with its error codes."""
    session = make_session(tmp_path)
    seed(session)
    good = call(
        session, "verify_derivation", {"claim_id": "C-01", "proof": valid_proof()}
    )
    assert good["valid"] is True
    assert good["errors"] == []
    bad_proof = valid_proof()
    bad_proof["premises"][0]["statement"] = "Clause 9.2 forbids transfer."
    bad = call(session, "verify_derivation", {"claim_id": "C-01", "proof": bad_proof})
    assert bad["valid"] is False
    assert bad["errors"][0]["code"] == "PREMISE_MISMATCH"
    session.close()


def test_propose_finding_accepts_and_rejects(tmp_path: Path) -> None:
    """T2.4: a valid draft is accepted; an invalid one is refused with a reason."""
    session = make_session(tmp_path)
    seed(session)
    accepted = call(
        session, "propose_finding", {"claim_id": "C-01", "proof": valid_proof()}
    )
    assert accepted == {"accepted": True}
    bad_proof = valid_proof()
    bad_proof["steps"] = []
    refused = call(
        session, "propose_finding", {"claim_id": "C-01", "proof": bad_proof}
    )
    assert refused["accepted"] is False
    assert "rejection_reason" in refused
    session.close()


def test_request_lawyer_review_creates_review(tmp_path: Path) -> None:
    """T2.4: flagging a claim writes a review row and returns its id."""
    session = make_session(tmp_path)
    seed(session)
    result = call(
        session,
        "request_lawyer_review",
        {"item_type": "claim", "item_id": "C-01", "reason": "Please confirm."},
    )
    review = session.get(models.Review, result["review_id"])
    assert review is not None
    assert review.item_type == "claim"
    assert review.status == "open"
    with pytest.raises(ToolError):
        call(
            session,
            "request_lawyer_review",
            {"item_type": "email", "item_id": "C-01", "reason": "Bad type."},
        )
    session.close()


def test_list_dependent_claims_scoped_to_matter(tmp_path: Path) -> None:
    """T2.4: dependents come only from the session matter via DEPENDS_ON edges."""
    session = make_session(tmp_path)
    seed(session)
    empty = call(session, "list_dependent_claims", {"source_id": "SRC-01"})
    assert empty == {"items": []}
    session.add(
        models.Finding(
            id="FND-01",
            claim_id="C-01",
            version_no=1,
            status="FOLLOWS",
            confidence_band="high",
            proof_json=None,
            as_of="2027-06-01",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.FindingEvent(
            id="FE-01",
            finding_id="FND-01",
            state="CURRENT",
            reason="decided",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Edge(
            id="E-01",
            src_type="finding",
            src_id="FND-01",
            dst_type="provision",
            dst_id="PRV-21",
            rel="DEPENDS_ON",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.commit()
    result = call(
        session,
        "list_dependent_claims",
        {"source_id": "SRC-01", "provision_key": "Section 1"},
    )
    assert result == {
        "items": [{"claim_id": "C-01", "finding_id": "FND-01", "state": "CURRENT"}]
    }
    with pytest.raises(SourceUnavailable):
        call(session, "list_dependent_claims", {"source_id": "SRC-NOPE"})
    session.close()


def test_calls_logged_to_tool_calls(tmp_path: Path) -> None:
    """T2.4: every dispatched call lands in `tool_calls` with seq and outcome."""
    session = make_session(tmp_path)
    seed(session)
    call(session, "lookup_source", {"source_id": "SRC-01"})
    with pytest.raises(ToolError):
        call(session, "browse_web", {})
    rows = tool_rows(session)
    assert [row.seq for row in rows] == [1, 2]
    assert [row.ok for row in rows] == [True, False]
    assert [row.tool for row in rows] == ["lookup_source", "browse_web"]
    assert rows[0].args_json == {"source_id": "SRC-01"}
    logged_result = rows[0].result_json
    assert isinstance(logged_result, dict)
    assert logged_result["source_version_id"] == "SV-02"
    session.close()
