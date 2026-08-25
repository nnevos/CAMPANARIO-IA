from fastapi.testclient import TestClient

from campanario.main import app


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_serves_web_chat() -> None:
    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert "CAMPANÁRIO" in response.text
    assert "/api/sessions" in response.text
