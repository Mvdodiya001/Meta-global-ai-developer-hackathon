"""Identity domain (Rewrite P1): tenants, users, roles, sessions, keys.

Owns: who you are and which tenant/matters you may touch.
P1 state: the `tenants` table and tenant-scoping helpers exist; every
row written before auth lands belongs to the demo tenant. The gateway
will resolve a `Principal` per request and inject its tenant; until
then `current_tenant_id()` returns the demo tenant.

Public interface: `DEMO_TENANT_ID`, `current_tenant_id`,
`ensure_tenant`, `tenant_query` (scope a SELECT to a tenant).
Forbidden: deciding findings, storing documents, calling models.
"""

from typing import Any

from sqlalchemy.orm import Session

from app import models

DEMO_TENANT_ID = "demo"


def current_tenant_id() -> str:
    """Tenant for the current request (demo until auth lands in P1+)."""
    return DEMO_TENANT_ID


def ensure_tenant(session: Session, tenant_id: str = DEMO_TENANT_ID, name: str = "Demo") -> str:
    """Insert the tenant row if missing; return its id (P1)."""
    if session.get(models.Tenant, tenant_id) is None:
        session.add(models.Tenant(id=tenant_id, name=name))
        session.commit()
    return tenant_id


def tenant_query(statement: Any, model: Any, tenant_id: str) -> Any:
    """Scope a SELECT to one tenant (model must carry tenant_id) (P1)."""
    return statement.where(model.tenant_id == tenant_id)


__all__ = [
    "DEMO_TENANT_ID",
    "current_tenant_id",
    "ensure_tenant",
    "tenant_query",
]
