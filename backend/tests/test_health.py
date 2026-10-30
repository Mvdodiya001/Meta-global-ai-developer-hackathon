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
