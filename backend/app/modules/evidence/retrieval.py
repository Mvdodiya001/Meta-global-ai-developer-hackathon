"""Phase 3: provision retrieval — find candidate sections for any text.

Deterministic token-overlap ranking over the current (non-simulated)
version of every source. No model call: the same query always returns
the same ranked list, on SQLite and Postgres alike, so results are
testable offline and identical in replay. The agent's `lookup_source`
tool uses this when given a `query`; the Review screen exposes it as
"Relevant sections".
"""

import re
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import models

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "by", "on",
    "shall", "may", "any", "such", "this", "that", "with", "from", "under",
    "section", "clause", "does", "do", "is", "are", "be", "as", "at", "it",
    "her", "his", "their", "who", "what", "when", "which", "into", "than",
    "then", "them", "they", "been", "being", "have", "has", "had", "not",
    "no", "if", "so", "per", "via", "etc", "one", "two", "all", "each",
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Legal concept map (Phase 3 semantic layer): wording a lawyer uses vs
# wording the statute uses. Expansion adds concept mates at lower weight
# so "sending data abroad" reaches "transfer ... outside India".
CONCEPTS: list[set[str]] = [
    {"abroad", "overseas", "transfer", "transfers", "outside", "india", "crossborder", "foreign"},
    {"leak", "leaked", "breach", "intimation", "intimate", "incident"},
    {"erase", "erasure", "delete", "deletion", "remove", "removal", "forget", "forgotten"},
    {"consent", "permission", "agree", "agreement", "authorisation", "authorization"},
    {"withdraw", "withdrawal", "revoke", "revocation", "optout"},
    {"child", "children", "minor", "guardian", "parental"},
    {"penalty", "penalties", "fine", "compensation", "damages", "liable", "liability"},
    {"assign", "assignment", "assignee", "assignor", "transfer", "ownership"},
    {"licence", "license", "licensing", "permission", "grant"},
    {"infringe", "infringement", "piracy", "unauthorised", "unauthorized"},
    {"intermediary", "platform", "hosting", "safe", "harbour", "harbor"},
    {"encrypt", "encryption", "safeguards", "security", "protect", "protection"},
    {"retain", "retention", "keep", "keeping", "store", "storage", "logs"},
    {"access", "obtain", "summary", "disclosure", "share", "sharing"},
    {"correct", "correction", "update", "updating", "rectify", "inaccurate"},
    {"grievance", "complaint", "redressal", "complain"},
    {"employer", "employment", "employee", "workplace"},
    {"government", "state", "sovereignty", "exemption", "exempt"},
]


def expand_tokens(query_tokens: set[str]) -> dict[str, float]:
    """Token weights after concept expansion (mates weigh less)."""
    weights: dict[str, float] = {token: 1.0 for token in query_tokens}
    for concept in CONCEPTS:
        if query_tokens & concept:
            for token in concept:
                weights.setdefault(token, 0.6)
    return weights


def tokenize(text: str) -> set[str]:
    """Content tokens of a text (Phase 3)."""
    return {
        token
        for token in _TOKEN_RE.findall(text.lower())
        if len(token) > 2 and token not in STOPWORDS
    }


def current_version_ids(session: Session) -> set[str]:
    """Non-simulated, non-superseded source version ids (Phase 3).

    A simulated amendment does not supersede the real version for
    retrieval: the enacted text stays the current law to search.
    """
    versions = session.execute(sa.select(models.SourceVersion)).scalars().all()
    superseded = {
        str(row.supersedes_id)
        for row in versions
        if row.supersedes_id is not None and not row.is_simulated
    }
    return {
        str(row.id)
        for row in versions
        if not row.is_simulated and str(row.id) not in superseded
    }


def search_provisions(
    session: Session,
    query: str,
    *,
    source_id: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Ranked provisions for a query, best first (Phase 3)."""
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    version_ids = current_version_ids(session)
    rows = session.execute(
        sa.select(models.Provision, models.Source, models.SourceVersion)
        .join(
            models.SourceVersion,
            models.Provision.source_version_id == models.SourceVersion.id,
        )
        .join(models.Source, models.SourceVersion.source_id == models.Source.id)
        .where(models.Provision.source_version_id.in_(version_ids))
    ).all()
    # IDF-weighted hit score over concept-expanded tokens: rare terms
    # count more, long provisions are not penalised for covering their
    # topic thoroughly, and statute wording reaches lawyer wording.
    import math

    weights = expand_tokens(query_tokens)
    expanded = set(weights)
    token_sets: list[set[str]] = []
    for provision, _source, _version in rows:
        token_sets.append(tokenize(f"{provision.key} {provision.text}"))
    doc_freq: dict[str, int] = {}
    for token_set in token_sets:
        for token in expanded & token_set:
            doc_freq[token] = doc_freq.get(token, 0) + 1
    total = max(1, len(rows))

    def idf(token: str) -> float:
        return math.log(1 + total / max(1, doc_freq.get(token, 1)))

    # Concept-collapsed bonus: each query-touched concept whose mates
    # appear in a provision adds half the anchor term's IDF — unless the
    # anchor itself already matched exactly (then it was rewarded in
    # `primary`). Expansion surfaces sections without outranking exact
    # statutory matches.
    touched: list[tuple[str, set[str]]] = []
    for concept in CONCEPTS:
        anchors = query_tokens & concept
        if anchors:
            touched.append((sorted(anchors)[0], concept))

    scored: list[dict[str, Any]] = []
    for (provision, source, version), provision_tokens in zip(rows, token_sets, strict=True):
        if source_id is not None and str(source.id) != source_id:
            continue
        matched = expanded & provision_tokens
        if not matched:
            continue
        primary = sum(idf(token) for token in query_tokens & provision_tokens)
        bonus = 0.0
        for anchor, concept in touched:
            if anchor not in provision_tokens and concept & provision_tokens:
                bonus += 0.5 * idf(anchor)
        score = round((primary + bonus) / max(1.0, len(query_tokens) ** 0.5), 4)
        scored.append(
            {
                "provision_id": str(provision.id),
                "key": str(provision.key),
                "source_id": str(source.id),
                "source_title": str(source.title),
                "source_version_id": str(version.id),
                "version_label": str(version.version_label),
                "score": score,
                "text": str(provision.text),
                "sha256": str(provision.text_sha256),
            }
        )
    scored.sort(key=lambda row: (-row["score"], row["key"]))
    return scored[:limit]
