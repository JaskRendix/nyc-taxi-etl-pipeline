from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.locations import router
from backend.core.db import get_db


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(mock_db):
    app = FastAPI()
    app.include_router(router, prefix="/api")

    # Override the get_db dependency for all requests made by the TestClient
    app.dependency_overrides[get_db] = lambda: mock_db

    yield TestClient(app)

    app.dependency_overrides.clear()


def mock_row(**kwargs):
    obj = MagicMock()
    for k, v in kwargs.items():
        setattr(obj, k, v)
    return obj


def test_top_locations_basic(client, mock_db):
    pu_rows = [(10, 100), (20, 50)]
    do_rows = [(30, 80), (40, 60)]
    mock_db.query.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.side_effect = [
        pu_rows,
        do_rows,
    ]

    r = client.get("/api/top-locations?limit=2")
    data = r.json()
    assert r.status_code == 200
    assert len(data["top_pickups"]) == 2
    assert len(data["top_dropoffs"]) == 2
    assert data["top_pickups"][0]["location"] == 10


def test_top_locations_empty(client, mock_db):
    mock_db.query.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.side_effect = [
        [],
        [],
    ]

    r = client.get("/api/top-locations")
    assert r.status_code == 200
    assert r.json() == {"top_pickups": [], "top_dropoffs": []}


def test_heatmap_data_basic(client, mock_db):
    rows = [(1, 100, 200, 50), (2, 101, 201, 60)]
    mock_db.query.return_value.group_by.return_value.limit.return_value.all.return_value = (
        rows
    )

    r = client.get("/api/heatmap-data?limit=2")
    data = r.json()
    assert r.status_code == 200
    assert len(data) == 2
    assert data[0]["hour"] == 1
    assert data[0]["count"] == 50


def test_heatmap_data_empty(client, mock_db):
    mock_db.query.return_value.group_by.return_value.limit.return_value.all.return_value = (
        []
    )

    r = client.get("/api/heatmap-data")
    assert r.status_code == 200
    assert r.json() == []


def test_location_pairs_basic(client, mock_db):
    rows = [(10, 20, 100), (11, 21, 50)]
    mock_db.query.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = (
        rows
    )

    r = client.get("/api/location-pairs?limit=2")
    data = r.json()
    assert r.status_code == 200
    assert len(data) == 2
    assert data[0]["pickup"] == 10
    assert data[0]["dropoff"] == 20


def test_location_pairs_empty(client, mock_db):
    mock_db.query.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = (
        []
    )

    r = client.get("/api/location-pairs")
    assert r.status_code == 200
    assert r.json() == []


def test_hotspot_corridors_basic(client, mock_db):
    rows = [(10, 20, 100, 15.0, 30.0), (11, 21, 80, 12.0, 25.0)]
    mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = (
        rows
    )

    r = client.get("/api/hotspot-corridors?limit=2")
    data = r.json()
    assert r.status_code == 200
    assert len(data) == 2
    assert data[0]["trip_count"] == 100
    assert data[0]["avg_fare"] == 15.0
    assert data[0]["avg_speed_mph"] == 30.0


def test_hotspot_corridors_empty(client, mock_db):
    mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = (
        []
    )

    r = client.get("/api/hotspot-corridors")
    assert r.status_code == 200
    assert r.json() == []


def test_airport_traffic_basic(client, mock_db):
    mock_db.query.return_value.filter.return_value.scalar.side_effect = [
        10,
        20,
        5,
        15,
        2,
        8,
    ]
    hourly_rows = [(0, 100), (1, 200)]
    mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = (
        hourly_rows
    )

    r = client.get("/api/airport-traffic")
    data = r.json()
    assert r.status_code == 200
    assert set(data.keys()) == {"JFK", "LGA", "EWR"}
    assert data["JFK"]["pickup_count"] == 10
    assert len(data["JFK"]["hourly_distribution"]) == 2


def test_airport_traffic_deep_dive_basic(client, mock_db):
    mock_db.query.return_value.filter.return_value.scalar.side_effect = [
        20.0,
        300.0,
        15.0,
        250.0,
        10.0,
        200.0,
    ]
    peak_rows = [(0, 100), (1, 90), (2, 80)]
    mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = (
        peak_rows
    )

    r = client.get("/api/airport-traffic-deep-dive")
    data = r.json()
    assert r.status_code == 200
    assert "JFK" in data
    assert data["JFK"]["avg_fare"] == 20.0
    assert len(data["JFK"]["peak_hours"]) == 3


def test_cluster_hints_basic(client, mock_db):
    rows = [(0, 1.0, 10.0, 300.0), (1, 2.0, 12.0, 350.0)]
    mock_db.query.return_value.group_by.return_value.order_by.return_value.all.return_value = (
        rows
    )

    r = client.get("/api/cluster-hints")
    data = r.json()
    assert r.status_code == 200
    assert len(data) == 2
    assert data[0]["avg_distance"] == 1.0


def test_rush_hour_squeeze_basic(client, mock_db):
    rows = [
        mock_row(id=1, trip_distance=0.5, trip_duration=1500, fare_amount=25.0, hour=8),
        mock_row(id=2, trip_distance=0.3, trip_duration=2000, fare_amount=30.0, hour=9),
    ]
    mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = (
        rows
    )

    r = client.get("/api/rush-hour-squeeze?limit=2")
    data = r.json()
    assert r.status_code == 200
    assert len(data) == 2
    assert data[0]["fare"] == 25.0


def test_rush_hour_squeeze_empty(client, mock_db):
    mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = (
        []
    )

    r = client.get("/api/rush-hour-squeeze")
    assert r.status_code == 200
    assert r.json() == []


def test_late_night_surges_basic(client, mock_db):
    rows = [
        mock_row(id=1, trip_distance=6.0, fare_amount=40.0, payment_type=2, hour=2),
        mock_row(id=2, trip_distance=7.0, fare_amount=50.0, payment_type=2, hour=3),
    ]
    mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = (
        rows
    )

    r = client.get("/api/late-night-surges?limit=2")
    data = r.json()
    assert r.status_code == 200
    assert len(data) == 2
    assert data[0]["payment_type"] == 2


def test_late_night_surges_empty(client, mock_db):
    mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = (
        []
    )

    r = client.get("/api/late-night-surges")
    assert r.status_code == 200
    assert r.json() == []


def test_too_good_to_be_true_basic(client, mock_db):
    rows = [
        mock_row(id=1, trip_distance=12.0, fare_amount=5.0, hour=10),
        mock_row(id=2, trip_distance=15.0, fare_amount=8.0, hour=11),
    ]
    mock_db.query.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = (
        rows
    )

    r = client.get("/api/too-good-to-be-true?limit=2")
    data = r.json()
    assert r.status_code == 200
    assert len(data) == 2
    assert data[0]["fare"] == 5.0


def test_too_good_to_be_true_empty(client, mock_db):
    mock_db.query.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = (
        []
    )

    r = client.get("/api/too-good-to-be-true")
    assert r.status_code == 200
    assert r.json() == []
