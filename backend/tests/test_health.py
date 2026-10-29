"""T0.4: health endpoint tests (written first)."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok() -> None:
    """T0.4: GET /api/health reports liveness (DATA_MODEL_API §7)."""
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
