"""Phase 3 semantic layer: AI re-ranking of retrieved provisions.

Classic RAG shape: deterministic retrieval first (fast, testable), then
one gateway call re-orders the shortlist by *meaning* and says why each
section fits. Any failure — mock mode, replay cassette miss, bad JSON —
falls back to the lexical order silently: retrieval must never break
because the re-ranker could not speak.
"""

import json
import re
from typing import Any

from sqlalchemy.orm import Session


def _prompt(query: str, hits: list[dict[str, Any]]) -> dict[str, Any]:
    listing = "\n".join(
        f"- {hit['provision_id']} ({hit['key']}): {hit['text'][:220]}" for hit in hits
    )
    return {
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Rank these legal provisions by how well they answer the query, "
                            "best first. Reply with JSON only: "
                            '{"order": ["provision_id", ...], '
                            '"why": {"provision_id": "one short reason"}}. '
                            "Include every id exactly once.\n\n"
                            f"Query: {query}\n\n{listing}"
                        ),
                    }
                ],
            }
        ]
    }


def rerank_hits(
    session: Session | None,
    query: str,
    hits: list[dict[str, Any]],
    *,
    mode: str | None = None,
) -> list[dict[str, Any]]:
    """Re-order hits semantically; lexical order on any failure."""
    if len(hits) < 2:
        return hits
    from app.agent import llm

    if llm.resolve_mode(mode) == "mock":
        return hits
    try:
        response = llm.call_llm(_prompt(query, hits), mode=mode, session=session, role="rerank")
        match = re.search(r"\{.*\}", response.text, re.DOTALL)
        if not match:
            return hits
        data = json.loads(match.group(0))
        order = [str(item) for item in data.get("order", [])]
        why = {str(k): str(v)[:200] for k, v in dict(data.get("why", {})).items()}
    except Exception:
        return hits
    by_id = {hit["provision_id"]: hit for hit in hits}
    if set(order) != set(by_id):
        return hits
    return [
        {**by_id[provision_id], "why": why.get(provision_id, ""), "reranked": True}
        for provision_id in order
    ]
