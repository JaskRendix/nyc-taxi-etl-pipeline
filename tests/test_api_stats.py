from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.stats import router
from backend.core.db import get_db


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(mock_db):
    app = FastAPI()
    app.include_router(router, prefix="/api")

    # Properly override the dependency for all requests made by the TestClient
    app.dependency_overrides[get_db] = lambda: mock_db

    yield TestClient(app)

    app.dependency_overrides.clear()


def test_stats_basic(client, mock_db):
    mock_db.query.return_value.scalar.side_effect = [100, 12.5]

    r = client.get("/api/stats")
    data = r.json()
    assert data["rows"] == 100
    assert data["avg_fare"] == 12.5


def test_stats_zero(client, mock_db):
    mock_db.query.return_value.scalar.side_effect = [None, None]

    r = client.get("/api/stats")
    data = r.json()
    assert data["rows"] == 0
    assert data["avg_fare"] == 0.0


def test_trip_distance_stats_basic(client, mock_db):
    mock_db.query.return_value.one.return_value = (1.0, 3.0, 10.0)

    r = client.get("/api/trip-distance-stats")
    data = r.json()
    assert data["min"] == 1.0
    assert data["avg"] == 3.0
    assert data["max"] == 10.0


def test_trip_distance_stats_nulls(client, mock_db):
    mock_db.query.return_value.one.return_value = (None, None, None)

    r = client.get("/api/trip-distance-stats")
    data = r.json()
    assert data["min"] == 0.0
    assert data["avg"] == 0.0
    assert data["max"] == 0.0


def test_payment_types_basic(client, mock_db):
    mock_db.query.return_value.group_by.return_value.all.return_value = [
        (1, 50),
        (2, 30),
    ]

    r = client.get("/api/payment-types")
    assert r.json() == {"1": 50, "2": 30}


def test_payment_types_empty(client, mock_db):
    mock_db.query.return_value.group_by.return_value.all.return_value = []

    r = client.get("/api/payment-types")
    assert r.json() == {}


def test_hourly_distribution_basic(client, mock_db):
    mock_db.query.return_value.group_by.return_value.order_by.return_value.all.return_value = [
        (0, 100),
        (1, 150),
    ]

    r = client.get("/api/hourly-distribution")
    data = r.json()
    assert len(data) == 2
    assert data[0]["hour"] == 0
    assert data[0]["count"] == 100


def test_hourly_distribution_empty(client, mock_db):
    mock_db.query.return_value.group_by.return_value.order_by.return_value.all.return_value = (
        []
    )

    r = client.get("/api/hourly-distribution")
    assert r.json() == []


def test_day_of_week_trends_basic(client, mock_db):
    mock_db.query.return_value.group_by.return_value.order_by.return_value.all.return_value = [
        (1, 100, 12.0, 300.0),
        (2, 150, 15.0, 350.0),
    ]

    r = client.get("/api/day-of-week-trends")
    data = r.json()
    assert len(data) == 2
    assert data[0]["day_of_week"] == 1
    assert data[0]["avg_fare"] == 12.0


def test_day_of_week_trends_empty(client, mock_db):
    mock_db.query.return_value.group_by.return_value.order_by.return_value.all.return_value = (
        []
    )

    r = client.get("/api/day-of-week-trends")
    assert r.json() == []


def test_shift_analysis_basic(client, mock_db):
    mock_db.query.return_value.group_by.return_value.all.return_value = [
        ("Morning Rush", 100, 12.0, 3.0, 300.0),
        ("Midday", 150, 15.0, 4.0, 350.0),
    ]

    r = client.get("/api/shift-analysis")
    data = r.json()
    assert len(data) == 2
    assert data[0]["shift"] == "Morning Rush"
    assert data[0]["avg_fare"] == 12.0


def test_shift_analysis_empty(client, mock_db):
    mock_db.query.return_value.group_by.return_value.all.return_value = []

    r = client.get("/api/shift-analysis")
    assert r.json() == []


def test_tip_stats_basic(client, mock_db):
    # Setup mock query execution chain for multiple queries
    query_mock = mock_db.query.return_value

    # First query (.scalar()) -> 5.0
    # Second query (.filter().scalar()) -> 0.2
    # Third query (.group_by().order_by().all()) -> hourly list
    query_mock.scalar.side_effect = [5.0, 0.2]
    query_mock.filter.return_value.scalar.return_value = 0.2
    query_mock.group_by.return_value.order_by.return_value.all.return_value = [
        (0, 1.0),
        (1, 2.0),
    ]

    r = client.get("/api/tip-stats")
    data = r.json()
    assert data["avg_tip"] == 5.0
    assert data["avg_tip_pct"] == 0.2
    assert len(data["avg_tip_by_hour"]) == 2


def test_tip_stats_empty(client, mock_db):
    query_mock = mock_db.query.return_value
    query_mock.scalar.side_effect = [None, None]
    query_mock.filter.return_value.scalar.return_value = None
    query_mock.group_by.return_value.order_by.return_value.all.return_value = []

    r = client.get("/api/tip-stats")
    data = r.json()
    assert data["avg_tip"] == 0.0
    assert data["avg_tip_pct"] == 0.0
    assert data["avg_tip_by_hour"] == []


def test_duration_stats_basic(client, mock_db, monkeypatch):
    mock_db.query.return_value.one.return_value = (10.0, 20.0, 30.0)
    mock_db.query.return_value.group_by.return_value.order_by.return_value.all.return_value = [
        (0, 100.0),
        (1, 200.0),
    ]

    with patch(
        "backend.api.stats.bucket_query", return_value=[("0-5", 150.0), ("5-10", 250.0)]
    ):
        r = client.get("/api/duration-stats")
        data = r.json()
        assert data["min"] == 10.0
        assert len(data["duration_by_hour"]) == 2
        assert len(data["duration_by_distance_bucket"]) == 2


def test_duration_stats_empty(client, mock_db):
    mock_db.query.return_value.one.return_value = (None, None, None)
    mock_db.query.return_value.group_by.return_value.order_by.return_value.all.return_value = (
        []
    )

    with patch("backend.api.stats.bucket_query", return_value=[]):
        r = client.get("/api/duration-stats")
        data = r.json()
        assert data["min"] == 0.0
        assert data["duration_by_hour"] == []
        assert data["duration_by_distance_bucket"] == []
