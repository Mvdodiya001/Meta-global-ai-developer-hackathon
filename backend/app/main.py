"""T0.4: FastAPI application scaffold with liveness probe (DATA_MODEL_API §7)."""

import os

from fastapi import FastAPI

from app import schemas
from app.api import router as api_router
from app.stub import router as stub_router


def create_app() -> FastAPI:
    """Build the ClauseTrace FastAPI application (T0.4, T0.7, T4.5)."""
    app = FastAPI(title="ClauseTrace", version="v1")

    @app.get("/api/health", response_model=schemas.Health)
    def health() -> dict[str, str]:
        """Liveness probe (DATA_MODEL_API §7)."""
        return {"status": "ok"}

    if os.getenv("API_STUB", "1") == "1":
        app.include_router(stub_router)
    else:
        app.include_router(api_router)

    return app


app = create_app()
