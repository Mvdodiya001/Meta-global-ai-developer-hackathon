"""T0.4: FastAPI application scaffold with liveness probe (DATA_MODEL_API §7)."""

import os

from fastapi import FastAPI

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
    """Build the ClauseTrace FastAPI application (T0.4, T0.7, T4.5, ask-flow)."""
    app = FastAPI(title="ClauseTrace", version="v14")

    @app.middleware("http")
    async def _auth_gate(request, call_next):  # type: ignore[no-untyped-def]
        """Enforce sign-in only when CT_AUTH_REQUIRED=1 (Identity).

        Demo deployments leave this off; real ones turn it on and every
        /api route except the public list needs a valid bearer token.
        """
        import os

        from fastapi.responses import JSONResponse

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
