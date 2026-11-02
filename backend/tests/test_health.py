"""T0.4: health endpoint tests (written first)."""

import asyncio

import httpx

from app.main import app


async def _get(path: str) -> httpx.Response:
    """In-process ASGI GET (no starlette TestClient deprecation)."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path)


def test_health_returns_ok() -> None:
    """T0.4: GET /api/health reports liveness (DATA_MODEL_API §7)."""
    response = asyncio.run(_get("/api/health"))
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_and_health_alias() -> None:
    """Gate: GET / and GET /health answer instead of 404.

    Browsers, scanners and load balancers probe the root and bare /health;
    both point at the canonical /api/health so nothing 404s on arrival.
    """
    root = asyncio.run(_get("/"))
    assert root.status_code == 200
    assert root.json()["status"] == "ok"
    assert root.json()["health"] == "/api/health"
    alias = asyncio.run(_get("/health"))
    assert alias.status_code == 200
    assert alias.json() == {"status": "ok"}
