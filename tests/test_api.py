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


def test_top_locations():
    r = client.get("/api/top-locations?limit=5")
    assert r.status_code == 200
    data = r.json()
    assert "top_pickups" in data
    assert "top_dropoffs" in data


def test_tip_stats():
    r = client.get("/api/tip-stats")
    assert r.status_code == 200
    data = r.json()
    assert "avg_tip" in data
    assert "avg_tip_pct" in data
    assert "avg_tip_by_hour" in data


def test_duration_stats():
    r = client.get("/api/duration-stats")
    assert r.status_code == 200
    data = r.json()
    assert "min" in data
    assert "avg" in data
    assert "max" in data


def test_heatmap_data():
    r = client.get("/api/heatmap-data")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


def test_fraud_signals():
    r = client.get("/api/fraud-signals")
    assert r.status_code == 200
    data = r.json()
    assert "short_expensive" in data
    assert "cash_only" in data


def test_outlier_fares():
    r = client.get("/api/outlier-fares?limit=5")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


def test_duplicate_trips():
    r = client.get("/api/duplicate-trips")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_cluster_hints():
    r = client.get("/api/cluster-hints")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


def test_distance_buckets():
    r = client.get("/api/distance-buckets")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_fare_buckets():
    r = client.get("/api/fare-buckets")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_location_pairs():
    r = client.get("/api/location-pairs?limit=5")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


def test_airport_traffic():
    r = client.get("/api/airport-traffic")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)


def test_rush_hour_squeeze():
    r = client.get("/api/rush-hour-squeeze")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_late_night_surges():
    r = client.get("/api/late-night-surges")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_too_good_to_be_true():
    r = client.get("/api/too-good-to-be-true")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_schema():
    r = client.get("/api/schema")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:
        assert "name" in data[0]
        assert "type" in data[0]


def test_row_sample():
    r = client.get("/api/row-sample?n=3")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) <= 3


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "db" in data
