"""CORS for split hosting (Vercel frontend + own backend server).

CT_CORS_ORIGINS unset -> no CORS middleware (same-origin/proxy behaviour).
CT_CORS_ORIGINS set -> browsers on those origins may call the API.
"""

import asyncio

import httpx

from app.main import create_app


def _app_with(origins: str | None):
    import os

    if origins is None:
        os.environ.pop("CT_CORS_ORIGINS", None)
    else:
        os.environ["CT_CORS_ORIGINS"] = origins
    try:
        return create_app()
    finally:
        os.environ.pop("CT_CORS_ORIGINS", None)


async def _get(app, path: str, headers: dict[str, str]) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path, headers=headers)


def test_no_cors_by_default() -> None:
    """Same-origin default: no access-control headers are emitted."""
    response = asyncio.run(_get(_app_with(None), "/api/health", {"Origin": "https://x.vercel.app"}))
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_listed_origin_is_allowed() -> None:
    """CT_CORS_ORIGINS allow-list is reflected back to the browser."""
    app = _app_with("https://ct.example.com, https://ct-preview.vercel.app")
    response = asyncio.run(_get(app, "/api/health", {"Origin": "https://ct-preview.vercel.app"}))
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://ct-preview.vercel.app"


def test_unlisted_origin_gets_no_cors_headers() -> None:
    """Origins outside the allow-list get no CORS grant."""
    app = _app_with("https://ct.example.com")
    response = asyncio.run(_get(app, "/api/health", {"Origin": "https://evil.example"}))
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
