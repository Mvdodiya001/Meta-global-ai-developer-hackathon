"""T0.4: FastAPI application scaffold with liveness probe (DATA_MODEL_API §7)."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import schemas
from app.api import router as api_router
from app.stub import router as stub_router

_PUBLIC_PATHS = (
    "/api/health",
    "/health",
    "/",
    "/api/auth/login",
    "/api/auth/register",
    "/docs",
    "/openapi.json",
)


def create_app() -> FastAPI:
    """Build the ClauseTrace FastAPI application (T0.4, T0.7, T4.5, ask-flow).

    Cross-origin browsers (e.g. a Vercel-hosted frontend talking to this
    API on another host) need CORS headers: set CT_CORS_ORIGINS to a
    comma-separated allow-list (or "*" for open demos). Unset = no CORS
    middleware, preserving same-origin/proxy behaviour.
    """
    app = FastAPI(title="ClauseTrace", version="v22")

    # Phase 6: optional per-client write rate limit. CT_RATE_LIMIT_PER_MIN
    # unset/0 = off (demo + tests unaffected); production sets a ceiling.
    rate_limit = int(os.environ.get("CT_RATE_LIMIT_PER_MIN", "0") or "0")
    if rate_limit > 0:
        import time as _time

        buckets: dict[str, list[float]] = {}

        @app.middleware("http")
        async def _rate_limit(request, call_next):  # type: ignore[no-untyped-def]
            """Reject write bursts beyond the configured ceiling (P6)."""
            from fastapi.responses import JSONResponse

            if request.method in ("POST", "PUT", "PATCH") and request.url.path.startswith("/api"):
                key = request.client.host if request.client else "unknown"
                now = _time.monotonic()
                bucket = [t for t in buckets.get(key, []) if now - t < 60]
                if len(bucket) >= rate_limit:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": {
                                "code": "RATE_LIMITED",
                                "message": "too many requests; wait a minute and try again",
                            }
                        },
                    )
                bucket.append(now)
                buckets[key] = bucket
            return await call_next(request)

    @app.middleware("http")
    async def _auth_gate(request, call_next):  # type: ignore[no-untyped-def]
        """Enforce sign-in only when CT_AUTH_REQUIRED=1 (Identity).

        Demo deployments leave this off; real ones turn it on and every
        /api route except the public list needs a valid bearer token.
        """
        import os

        from fastapi.responses import JSONResponse

        if request.method == "OPTIONS":
            # CORS preflights carry no credentials by design; the CORS
            # layer (outermost) answers them. Never gate them here.
            return await call_next(request)
        if os.environ.get("CT_AUTH_REQUIRED", "0") == "1" and request.url.path.startswith("/api"):
            if not any(request.url.path == path for path in _PUBLIC_PATHS):
                header = request.headers.get("authorization", "")
                from app.modules.identity import auth

                if not header.startswith("Bearer ") or auth.decode_token(
                    header.removeprefix("Bearer ")
                ) is None:
                    return JSONResponse(
                        status_code=401,
                        content={"error": {"code": "AUTH_REQUIRED", "message": "sign-in required"}},
                    )
        return await call_next(request)

    # CORS is registered LAST so it is the outermost middleware: it must
    # answer preflights before the auth gate sees them, and its headers
    # must be present even on 401/429 responses generated inside —
    # otherwise browsers hide those responses from the SPA entirely.
    cors_origins = os.environ.get("CT_CORS_ORIGINS", "")
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[o.strip() for o in cors_origins.split(",") if o.strip()],
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/api/health", response_model=schemas.Health)
    def health() -> dict[str, str]:
        """Liveness probe (DATA_MODEL_API §7)."""
        return {"status": "ok"}

    @app.get("/health", response_model=schemas.Health)
    def health_alias() -> dict[str, str]:
        """Bare /health alias for load balancers and scanners (gate fix)."""
        return {"status": "ok"}

    @app.get("/")
    def root() -> dict[str, str]:
        """Service index so root probes do not 404 (gate fix)."""
        return {
            "status": "ok",
            "service": "ClauseTrace",
            "health": "/api/health",
            "docs": "/docs",
        }

    if os.getenv("API_STUB", "1") == "1":
        app.include_router(stub_router)
    else:
        app.include_router(api_router)

    return app


app = create_app()
