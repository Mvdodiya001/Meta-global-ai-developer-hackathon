"""Phase 3 semantic layer: AI re-ranking with silent lexical fallback."""

from typing import Any

from app.agent import llm
from app.modules.evidence import rerank

HITS: list[dict[str, Any]] = [
    {"provision_id": "PRV-A", "key": "A", "text": "alpha text"},
    {"provision_id": "PRV-B", "key": "B", "text": "beta text"},
    {"provision_id": "PRV-C", "key": "C", "text": "gamma text"},
]


class _Response:
    def __init__(self, text: str) -> None:
        self.text = text


def test_rerank_applies_model_order_and_reasons(monkeypatch) -> None:
    """Semantic layer: model order wins and carries a reason per hit."""
    monkeypatch.setattr(
        llm,
        "call_llm",
        lambda *args, **kwargs: _Response(
            '{"order": ["PRV-C", "PRV-A", "PRV-B"], "why": {"PRV-C": "closest meaning"}}'
        ),
    )
    out = rerank.rerank_hits(None, "query", HITS, mode="live")
    assert [hit["provision_id"] for hit in out] == ["PRV-C", "PRV-A", "PRV-B"]
    assert out[0]["why"] == "closest meaning"
    assert out[0]["reranked"] is True


def test_rerank_mock_mode_keeps_lexical_order(monkeypatch) -> None:
    """Mock mode never calls the model; lexical order stands."""

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("model must not be called in mock mode")

    monkeypatch.setattr(llm, "call_llm", forbidden)
    out = rerank.rerank_hits(None, "query", HITS, mode="mock")
    assert [hit["provision_id"] for hit in out] == ["PRV-A", "PRV-B", "PRV-C"]


def test_rerank_bad_output_falls_back(monkeypatch) -> None:
    """Unparseable model output falls back to lexical order silently."""
    monkeypatch.setattr(llm, "call_llm", lambda *args, **kwargs: _Response("not json at all"))
    out = rerank.rerank_hits(None, "query", HITS, mode="live")
    assert [hit["provision_id"] for hit in out] == ["PRV-A", "PRV-B", "PRV-C"]
