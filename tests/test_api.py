from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_stats_endpoint_returns_200():
    response = client.get("/api/stats")
    assert response.status_code == 200


def test_stats_endpoint_structure():
    response = client.get("/api/stats")
    data = response.json()
    assert "rows" in data
    assert "avg_fare" in data
