"""Per-tenant model spend budgets (Rewrite P5).

Spend is the sum of `llm_calls.cost_est` over the tenant's runs
(claims carry tenant_id). The limit comes from
`CT_TENANT_BUDGET_USD` (unset = no limit). Checking is explicit at
the agent-loop entry in live mode — replay and tests never trip it,
and exceeding the budget is a loud typed error, not a silent stop.
"""

import os

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import models
from app.core.errors import LLMRequestFailed


def spend_for_tenant(session: Session, tenant_id: str) -> float:
    """Total estimated model spend for one tenant in USD (P5)."""
    total = session.execute(
        sa.select(sa.func.coalesce(sa.func.sum(models.LlmCall.cost_est), 0.0))
        .join(models.Run, models.LlmCall.run_id == models.Run.id)
        .join(models.Claim, models.Run.claim_id == models.Claim.id)
        .where(models.Claim.tenant_id == tenant_id)
    ).scalar()
    return float(total or 0.0)


def budget_limit() -> float | None:
    """Configured per-tenant budget in USD, or None when unlimited (P5)."""
    raw = os.environ.get("CT_TENANT_BUDGET_USD")
    if raw is None or raw.strip() == "":
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def check_budget(session: Session, tenant_id: str) -> float:
    """Raise LLMRequestFailed if the tenant is over budget (P5)."""
    limit = budget_limit()
    spent = spend_for_tenant(session, tenant_id)
    if limit is not None and spent >= limit:
        raise LLMRequestFailed(
            f"tenant {tenant_id} is over its model budget "
            f"(${spent:.4f} spent of ${limit:.2f})"
        )
    return spent
