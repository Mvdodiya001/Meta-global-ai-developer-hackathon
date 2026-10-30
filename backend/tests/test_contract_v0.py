"""T0.7: contract v0 tests — version pin, example validity, stub parity."""

import asyncio
import json
from pathlib import Path
from typing import Any, cast

import httpx
import pytest

from app.main import app

REPO = Path(__file__).resolve().parents[2]
OPENAPI = REPO / "openapi" / "openapi.json"
EXAMPLES = REPO / "openapi" / "examples"


def load_openapi() -> dict[str, Any]:
    """Load the checked-in contract (T0.7)."""
    return cast("dict[str, Any]", json.loads(OPENAPI.read_text()))


def example(name: str) -> object:
    """Load one example payload (T0.7)."""
    return json.loads((EXAMPLES / name).read_text())


async def _request(method: str, path: str, body: object = None) -> httpx.Response:
    """In-process ASGI request (no starlette TestClient deprecation)."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        if method == "get":
            return await client.get(path)
        return await client.post(path, json=body)


def client_get(path: str) -> httpx.Response:
    """Synchronous wrapper for GET (T0.7)."""
    return asyncio.run(_request("get", path))


def client_post(path: str, body: object) -> httpx.Response:
    """Synchronous wrapper for POST (T0.7)."""
    return asyncio.run(_request("post", path, body))


def test_contract_version_is_v1() -> None:
    """Ask-flow: [CONTRACT v1 → v2] — ClaimCreated carries the loop finding."""
    assert load_openapi()["info"]["version"] == "v2"


def test_spec_paths_present() -> None:
    """T0.7: every DATA_MODEL_API §7 path is in the contract."""
    paths = load_openapi()["paths"]
    for path in [
        "/api/health",
        "/api/matters/{id}",
        "/api/matters/{id}/documents",
        "/api/documents/{id}/clauses",
        "/api/documents/{id}/extract",
        "/api/matters/{id}/facts",
        "/api/facts/{id}/approve",
        "/api/facts/{id}/challenge",
        "/api/facts/{id}/reject",
        "/api/claims",
        "/api/runs/{id}",
        "/api/runs/{id}/events",
        "/api/claims/{id}/current",
        "/api/claims/{id}/history",
        "/api/findings/{id}",
        "/api/findings/{id}/review",
        "/api/sources",
        "/api/sources/{id}/versions",
        "/api/source-versions/{id}/diff",
        "/api/sources/{id}/ingest",
        "/api/impact/{id}",
        "/api/impact/{id}/reverify",
        "/api/graph",
        "/api/audit",
        "/api/proofs/verify",
        "/api/counterfactual",
        "/api/demo/reset",
        "/api/demo/scenario/{name}",
    ]:
        assert path in paths, path


def test_examples_are_valid_json() -> None:
    """T0.7: every example payload parses."""
    files = sorted(EXAMPLES.glob("*.json"))
    assert files, "no example payloads"
    for path in files:
        assert isinstance(json.loads(path.read_text()), (dict, list)), path.name


GET_CASES = [
    ("/api/health", "health.json"),
    ("/api/matters/MAT-01", "matter.json"),
    ("/api/matters/MAT-01/documents", "documents.json"),
    ("/api/documents/DOC-01/clauses", "clauses.json"),
    ("/api/matters/MAT-01/facts", "facts.json"),
    ("/api/runs/RUN-01", "run.json"),
    ("/api/runs/RUN-01/events", "run_events.json"),
    ("/api/claims/C-001/current", "finding_current.json"),
    ("/api/claims/C-001/history", "finding_history.json"),
    ("/api/findings/FND-001", "finding.json"),
    ("/api/sources", "sources.json"),
    ("/api/sources/SRC-DPDP-ACT/versions", "source_versions.json"),
    ("/api/source-versions/SV-01/diff?against=SV-02", "diff.json"),
    ("/api/impact/IMP-01", "impact.json"),
    ("/api/graph?matter_id=MAT-01", "graph.json"),
    ("/api/audit?matter_id=MAT-01", "audit.json"),
]

POST_CASES = [
    ("/api/documents/DOC-01/extract", {}, "extract_result.json"),
    ("/api/facts/F-001/approve", {"note": "verified"}, "fact_action.json"),
    ("/api/facts/F-001/challenge", {"note": "check span"}, "fact_action.json"),
    ("/api/facts/F-001/reject", {"note": "wrong clause"}, "fact_action.json"),
    (
        "/api/claims",
        {"clause_id": "CL-9.2", "question": "Does 9.2 meet consent rules?", "as_of": "2025-10-01"},
        "claim_created.json",
    ),
    ("/api/findings/FND-001/review", {"action": "approve", "note": "ok"}, "review_result.json"),
    ("/api/sources/SRC-DPDP-ACT/ingest", {"fixture": "v2-simulated"}, "ingest_result.json"),
    ("/api/impact/IMP-01/reverify", {}, "reverify_result.json"),
    ("/api/proofs/verify", {"proof": {"conclusion": "holds"}}, "proofs_verify.json"),
    ("/api/counterfactual", {"provision_key": "Section 6"}, "counterfactual.json"),
]


@pytest.mark.parametrize(("path", "filename"), GET_CASES)
def test_stub_get_returns_example(path: str, filename: str) -> None:
    """T0.7: stub mode returns the checked-in examples."""
    response = client_get(path)
    assert response.status_code == 200, path
    assert response.json() == example(filename)


@pytest.mark.parametrize(("path", "body", "filename"), POST_CASES)
def test_stub_post_returns_example(path: str, body: dict, filename: str) -> None:
    """T0.7: stub mode returns the checked-in examples for writes."""
    response = client_post(path, body)
    assert response.status_code == 200, path
    assert response.json() == example(filename)
