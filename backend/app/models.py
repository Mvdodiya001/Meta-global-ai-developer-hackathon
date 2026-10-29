"""T1.1: SQLAlchemy 2 table models for every DATA_MODEL_API §2 table (F1–F18).

IDs are caller-supplied prefixed strings (`SRC-`, `SV-`, `PRV-`, …). Timestamps
are UTC ISO-8601 strings; legal dates are plain-date strings. Append-only
enforcement lives in `app.db` as SQLite triggers, not in these models.
"""

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for ClauseTrace tables (T1.1)."""


class Matter(Base):
    """A client matter (F18)."""

    __tablename__ = "matters"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    client_name: Mapped[str] = mapped_column(sa.String, nullable=False)
    title: Mapped[str] = mapped_column(sa.String, nullable=False)


class MatterContext(Base):
    """Static hearing/task panel row, shown with a demo-data label (F18)."""

    __tablename__ = "matter_context"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    matter_id: Mapped[str] = mapped_column(sa.ForeignKey("matters.id"), nullable=False)
    kind: Mapped[str] = mapped_column(sa.String, nullable=False)
    title: Mapped[str] = mapped_column(sa.String, nullable=False)
    due_at: Mapped[str] = mapped_column(sa.String, nullable=False)
    source_label: Mapped[str] = mapped_column(sa.String, nullable=False)


class Source(Base):
    """A legal source in the registry (F1)."""

    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    key: Mapped[str] = mapped_column(sa.String, nullable=False, unique=True)
    title: Mapped[str] = mapped_column(sa.String, nullable=False)
    publisher: Mapped[str] = mapped_column(sa.String, nullable=False)
    url: Mapped[str] = mapped_column(sa.String, nullable=False)
    jurisdiction: Mapped[str] = mapped_column(sa.String, nullable=False)


class SourceVersion(Base):
    """One hashed source snapshot; append-only (F1, F11, F13)."""

    __tablename__ = "source_versions"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    source_id: Mapped[str] = mapped_column(sa.ForeignKey("sources.id"), nullable=False)
    version_label: Mapped[str] = mapped_column(sa.String, nullable=False)
    published_on: Mapped[str] = mapped_column(sa.String, nullable=False)
    effective_from: Mapped[str] = mapped_column(sa.String, nullable=False)
    effective_until: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    retrieved_at: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    content_sha256: Mapped[str] = mapped_column(sa.String, nullable=False)
    raw_text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    is_simulated: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    supersedes_id: Mapped[str | None] = mapped_column(sa.String, nullable=True)


class Provision(Base):
    """One provision inside a source version; append-only (F2)."""

    __tablename__ = "provisions"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    source_version_id: Mapped[str] = mapped_column(
        sa.ForeignKey("source_versions.id"), nullable=False
    )
    key: Mapped[str] = mapped_column(sa.String, nullable=False)
    text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    text_sha256: Mapped[str] = mapped_column(sa.String, nullable=False)
    effective_from: Mapped[str] = mapped_column(sa.String, nullable=False)
    effective_until: Mapped[str | None] = mapped_column(sa.String, nullable=True)


class RuleCard(Base):
    """A hand-curated card citing a verbatim span (F2)."""

    __tablename__ = "rule_cards"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    provision_id: Mapped[str] = mapped_column(sa.ForeignKey("provisions.id"), nullable=False)
    kind: Mapped[str] = mapped_column(sa.String, nullable=False)
    claim_type: Mapped[str] = mapped_column(sa.String, nullable=False)
    predicate_json: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    interpretation_text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    span_start: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    span_end: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    trust_class: Mapped[str] = mapped_column(sa.String, nullable=False)
    approved_by: Mapped[str] = mapped_column(sa.String, nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String, nullable=False)
    superseded_by: Mapped[str | None] = mapped_column(sa.String, nullable=True)


class Document(Base):
    """A contract document in a matter (F3)."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    matter_id: Mapped[str] = mapped_column(sa.ForeignKey("matters.id"), nullable=False)
    title: Mapped[str] = mapped_column(sa.String, nullable=False)
    kind: Mapped[str] = mapped_column(sa.String, nullable=False)


class DocumentVersion(Base):
    """One hashed snapshot of a document (F3)."""

    __tablename__ = "document_versions"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    document_id: Mapped[str] = mapped_column(sa.ForeignKey("documents.id"), nullable=False)
    text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    sha256: Mapped[str] = mapped_column(sa.String, nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String, nullable=False)


class Clause(Base):
    """One extracted clause with its span (F3)."""

    __tablename__ = "clauses"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    document_version_id: Mapped[str] = mapped_column(
        sa.ForeignKey("document_versions.id"), nullable=False
    )
    ref: Mapped[str] = mapped_column(sa.String, nullable=False)
    heading: Mapped[str] = mapped_column(sa.String, nullable=False)
    text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    span_start: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    span_end: Mapped[int] = mapped_column(sa.Integer, nullable=False)


class Fact(Base):
    """A premise candidate; a trust change is a new row (F8, F15)."""

    __tablename__ = "facts"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    matter_id: Mapped[str] = mapped_column(sa.ForeignKey("matters.id"), nullable=False)
    clause_id: Mapped[str | None] = mapped_column(sa.ForeignKey("clauses.id"), nullable=True)
    statement: Mapped[str] = mapped_column(sa.Text, nullable=False)
    structured_json: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    origin: Mapped[str] = mapped_column(sa.String, nullable=False)
    trust_class: Mapped[str] = mapped_column(sa.String, nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String, nullable=False)
    approved_by: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    approved_at: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    supersedes_id: Mapped[str | None] = mapped_column(sa.String, nullable=True)


class Claim(Base):
    """A structured question about a clause (F4)."""

    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    matter_id: Mapped[str] = mapped_column(sa.ForeignKey("matters.id"), nullable=False)
    clause_id: Mapped[str] = mapped_column(sa.ForeignKey("clauses.id"), nullable=False)
    claim_type: Mapped[str] = mapped_column(sa.String, nullable=False)
    params_json: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    question_text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    as_of: Mapped[str] = mapped_column(sa.String, nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String, nullable=False)


class Finding(Base):
    """One decided finding version; append-only, never updated (F7)."""

    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    claim_id: Mapped[str] = mapped_column(sa.ForeignKey("claims.id"), nullable=False)
    version_no: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    status: Mapped[str] = mapped_column(sa.String, nullable=False)
    confidence_band: Mapped[str] = mapped_column(sa.String, nullable=False)
    proof_json: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    as_of: Mapped[str] = mapped_column(sa.String, nullable=False)
    source_version_ids_json: Mapped[list | None] = mapped_column(sa.JSON, nullable=True)
    premise_ids_json: Mapped[list | None] = mapped_column(sa.JSON, nullable=True)
    rule_card_ids_json: Mapped[list | None] = mapped_column(sa.JSON, nullable=True)
    checker_report_json: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    run_id: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    created_at: Mapped[str] = mapped_column(sa.String, nullable=False)
    supersedes_finding_id: Mapped[str | None] = mapped_column(sa.String, nullable=True)


class FindingEvent(Base):
    """Append-only state log for findings (F11, F12, F16)."""

    __tablename__ = "finding_events"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    finding_id: Mapped[str] = mapped_column(sa.ForeignKey("findings.id"), nullable=False)
    state: Mapped[str] = mapped_column(sa.String, nullable=False)
    reason: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    caused_by_type: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    caused_by_id: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    created_at: Mapped[str] = mapped_column(sa.String, nullable=False)


class ChallengerReport(Base):
    """Second-pass Muse Spark objections (F17)."""

    __tablename__ = "challenger_reports"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    claim_id: Mapped[str] = mapped_column(sa.ForeignKey("claims.id"), nullable=False)
    finding_id: Mapped[str | None] = mapped_column(sa.ForeignKey("findings.id"), nullable=True)
    model: Mapped[str] = mapped_column(sa.String, nullable=False)
    objections_json: Mapped[list | None] = mapped_column(sa.JSON, nullable=True)
    created_at: Mapped[str] = mapped_column(sa.String, nullable=False)


class Edge(Base):
    """A typed graph edge between two items (F10)."""

    __tablename__ = "edges"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    src_type: Mapped[str] = mapped_column(sa.String, nullable=False)
    src_id: Mapped[str] = mapped_column(sa.String, nullable=False)
    dst_type: Mapped[str] = mapped_column(sa.String, nullable=False)
    dst_id: Mapped[str] = mapped_column(sa.String, nullable=False)
    rel: Mapped[str] = mapped_column(sa.String, nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String, nullable=False)


class Run(Base):
    """One verify/reverify agent run."""

    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    trigger: Mapped[str] = mapped_column(sa.String, nullable=False)
    claim_id: Mapped[str] = mapped_column(sa.ForeignKey("claims.id"), nullable=False)
    started_at: Mapped[str] = mapped_column(sa.String, nullable=False)
    ended_at: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    outcome: Mapped[str | None] = mapped_column(sa.String, nullable=True)


class ToolCall(Base):
    """One logged tool call; feeds re-query enforcement (F12)."""

    __tablename__ = "tool_calls"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    run_id: Mapped[str] = mapped_column(sa.ForeignKey("runs.id"), nullable=False)
    seq: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    tool: Mapped[str] = mapped_column(sa.String, nullable=False)
    args_json: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    result_json: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    ok: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String, nullable=False)


class LlmCall(Base):
    """Credit tracking for every model call."""

    __tablename__ = "llm_calls"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    run_id: Mapped[str | None] = mapped_column(sa.ForeignKey("runs.id"), nullable=True)
    role: Mapped[str] = mapped_column(sa.String, nullable=False)
    model: Mapped[str] = mapped_column(sa.String, nullable=False)
    request_sha256: Mapped[str] = mapped_column(sa.String, nullable=False)
    tokens_in: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    tokens_out: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    cost_est: Mapped[float] = mapped_column(sa.Float, nullable=False, default=0.0)
    latency_ms: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    cached: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)


class Review(Base):
    """A lawyer review action (F15, F16)."""

    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    item_type: Mapped[str] = mapped_column(sa.String, nullable=False)
    item_id: Mapped[str] = mapped_column(sa.String, nullable=False)
    reason: Mapped[str] = mapped_column(sa.Text, nullable=False)
    status: Mapped[str] = mapped_column(sa.String, nullable=False)
    reviewer: Mapped[str] = mapped_column(sa.String, nullable=False)
    note: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[str] = mapped_column(sa.String, nullable=False)


class AuditLog(Base):
    """Append-only audit trail; never updated (F14)."""

    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    ts: Mapped[str] = mapped_column(sa.String, nullable=False)
    actor_type: Mapped[str] = mapped_column(sa.String, nullable=False)
    actor_id: Mapped[str] = mapped_column(sa.String, nullable=False)
    event: Mapped[str] = mapped_column(sa.String, nullable=False)
    object_type: Mapped[str] = mapped_column(sa.String, nullable=False)
    object_id: Mapped[str] = mapped_column(sa.String, nullable=False)
    details_json: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
