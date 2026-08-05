from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.fraud import router
from backend.core.db import get_db


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(mock_db):
    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_db] = lambda: mock_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def mock_row(**kwargs):
    obj = MagicMock()
    for k, v in kwargs.items():
        setattr(obj, k, v)
    # SQLAlchemy Row objects expose a _mapping property
    obj._mapping = kwargs
    return obj


def test_fraud_signals_basic(client, mock_db):
    row_data = mock_row(
        total_trips=100,
        short_expensive=5,
        long_duration_short_distance=3,
        cash_only=10,
        zero_distance_nonzero_fare=2,
        identical_timestamps=1,
        no_passenger_count=4,
        high_tip_percentage=6,
        negative_fare=1,
        impossible_speed=2,
        very_high_total_amount=3,
    )

    # Since query = db.query(...); query = query.with_entities(...)
    # Both calls share mock_db.query.return_value as the base query object.
    mock_db.query.return_value.with_entities.return_value.one.return_value = row_data

    r = client.get("/api/fraud-signals")
    assert r.status_code == 200
    data = r.json()
    assert data["total_trips"] == 100
    assert data["signals"]["short_expensive"]["count"] == 5


def test_fraud_signals_zero_total(client, mock_db):
    row_data = mock_row(total_trips=0, short_expensive=5)
    mock_db.query.return_value.filter.return_value.with_entities.return_value.one.return_value = (
        row_data
    )

    r = client.get("/api/fraud-signals")
    assert r.status_code == 200
    data = r.json()
    if "short_expensive" in data.get("signals", {}):
        assert data["signals"]["short_expensive"]["percentage"] == 0.0
    else:
        assert data["total_trips"] == 0


def test_fraud_signals_date_filters(client, mock_db):
    row_data = mock_row(total_trips=10, short_expensive=1)
    mock_db.query.return_value.filter.return_value.filter.return_value.with_entities.return_value.one.return_value = (
        row_data
    )

    r = client.get(
        "/api/fraud-signals?start_date=2024-01-01T00:00:00&end_date=2024-01-02T00:00:00"
    )
    assert r.status_code == 200


def test_tip_outliers_basic(client, mock_db):
    mock_db.query.return_value.scalar.side_effect = [10.0, 2.0]
    rows = [
        mock_row(id=1, tip_amount=20.0, fare_amount=50.0, trip_distance=3.0),
        mock_row(id=2, tip_amount=25.0, fare_amount=60.0, trip_distance=4.0),
    ]
    mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = (
        rows
    )

    r = client.get("/api/tip-outliers?limit=2")
    assert r.status_code == 200
    assert len(r.json()) == 2
    assert r.json()[0]["id"] == 1


def test_tip_outliers_empty(client, mock_db):
    mock_db.query.return_value.scalar.side_effect = [0, 1]
    mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = (
        []
    )

    r = client.get("/api/tip-outliers?limit=5")
    assert r.status_code == 200
    assert r.json() == []


def test_route_circuitousness_basic(client, mock_db):
    rows = [
        mock_row(id=1, trip_distance=20.0, fare_amount=10.0, trip_duration=600),
        mock_row(id=2, trip_distance=18.0, fare_amount=15.0, trip_duration=500),
    ]
    mock_db.query.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = (
        rows
    )

    r = client.get("/api/route-circuitousness?limit=2")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_route_circuitousness_empty(client, mock_db):
    mock_db.query.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = (
        []
    )

    r = client.get("/api/route-circuitousness")
    assert r.status_code == 200
    assert r.json() == []


def test_fare_distance_anomalies_basic(client, mock_db):
    rows = [
        mock_row(id=1, trip_distance=0.3, fare_amount=60.0),
        mock_row(id=2, trip_distance=0.1, fare_amount=80.0),
    ]
    mock_db.query.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = (
        rows
    )

    r = client.get("/api/fare-to-distance-anomalies?limit=2")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_fare_distance_anomalies_empty(client, mock_db):
    mock_db.query.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = (
        []
    )

    r = client.get("/api/fare-to-distance-anomalies")
    assert r.status_code == 200
    assert r.json() == []
