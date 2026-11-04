"""v15: the models discovery endpoint never 404s (both paths)."""

from fastapi.testclient import TestClient

from app.agent import llm
from app.main import create_app


def _client() -> TestClient:
    return TestClient(create_app(), raise_server_exceptions=False)


def test_models_lists_default_model() -> None:
    """GET /api/models reports the gateway model and current mode."""
    response = _client().get("/api/models")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["models"][0]["id"] == llm.DEFAULT_MODEL
    assert body["models"][0]["provider"] == "meta"
    assert body["models"][0]["mode"] == "replay"


def test_v1_models_alias_matches() -> None:
    """GET /api/v1/models answers identically instead of 404."""
    client = _client()
    assert client.get("/api/v1/models").json() == client.get("/api/models").json()
