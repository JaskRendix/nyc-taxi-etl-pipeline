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


def test_trip_distance_stats():
    r = client.get("/api/trip-distance-stats")
    assert r.status_code == 200
    data = r.json()
    assert "min" in data
    assert "avg" in data
    assert "max" in data


def test_payment_types():
    r = client.get("/api/payment-types")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)


def test_hourly_distribution():
    r = client.get("/api/hourly-distribution")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:
        assert "hour" in data[0]
        assert "count" in data[0]
