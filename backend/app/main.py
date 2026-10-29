"""T0.4: FastAPI application scaffold with liveness probe (DATA_MODEL_API §7)."""

from fastapi import FastAPI


def create_app() -> FastAPI:
    """Build the ClauseTrace FastAPI application (T0.4)."""
    app = FastAPI(title="ClauseTrace")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        """Liveness probe (DATA_MODEL_API §7)."""
        return {"status": "ok"}

    return app


app = create_app()
