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
    assert "CAMPANARIO" in response.text
    assert "/api/v1/sessions" in TestClient(app).get("/static/chat.js").text
    assert "/ws/v1/events" in TestClient(app).get("/static/chat.js").text
    assert "/chat/stream" not in response.text
