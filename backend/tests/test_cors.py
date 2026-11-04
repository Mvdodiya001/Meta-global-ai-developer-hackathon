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


async def _request(app, method: str, path: str, headers: dict[str, str]) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.request(method, path, headers=headers)


def test_preflight_not_blocked_by_auth_gate(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Regression: with CT_AUTH_REQUIRED=1, a CORS preflight (OPTIONS, no
    credentials by design) must be answered by the CORS layer, not 401'd
    by the auth gate — otherwise browsers block every authenticated
    cross-origin request and the SPA reports a generic load failure."""
    monkeypatch.setenv("CT_AUTH_REQUIRED", "1")
    app = _app_with("https://ct.example.com")
    response = asyncio.run(
        _request(
            app,
            "OPTIONS",
            "/api/matters",
            {
                "Origin": "https://ct.example.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://ct.example.com"


def test_auth_401_carries_cors_headers(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Regression: a 401 from the auth gate must still carry CORS headers,
    or the browser hides the response and the SPA cannot tell the user
    to sign in."""
    monkeypatch.setenv("CT_AUTH_REQUIRED", "1")
    app = _app_with("https://ct.example.com")
    response = asyncio.run(
        _get(app, "/api/matters", {"Origin": "https://ct.example.com"})
    )
    assert response.status_code == 401
    assert response.headers["access-control-allow-origin"] == "https://ct.example.com"
