from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.samples import router
from backend.core.db import get_db


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(mock_db):
    app = FastAPI()
    app.include_router(router, prefix="/api")

    # Override the get_db dependency to use the mock_db fixture
    app.dependency_overrides[get_db] = lambda: mock_db

    yield TestClient(app)

    app.dependency_overrides.clear()


def mock_row(**kwargs):
    obj = MagicMock()
    for k, v in kwargs.items():
        setattr(obj, k, v)
    return obj


def test_outlier_fares_basic(client, mock_db):
    rows = [
        mock_row(id=1, fare_amount=100.0, trip_distance=2.0, fare_per_mile=50.0),
        mock_row(id=2, fare_amount=80.0, trip_distance=1.0, fare_per_mile=80.0),
    ]
    mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
        rows
    )

    r = client.get("/api/outlier-fares?limit=2&offset=0")
    data = r.json()
    assert r.status_code == 200
    assert len(data) == 2
    assert data[0]["fare_per_mile"] == 50.0


def test_outlier_fares_empty(client, mock_db):
    mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
        []
    )

    r = client.get("/api/outlier-fares")
    assert r.status_code == 200
    assert r.json() == []


def test_duplicate_trips_basic(client, mock_db):
    rows = [
        ("2024-01-01T00:00:00", "2024-01-01T00:10:00", 10, 20, 1, 3),
        ("2024-01-02T00:00:00", "2024-01-02T00:05:00", 11, 21, 2, 4),
    ]
    mock_db.query.return_value.group_by.return_value.having.return_value.offset.return_value.limit.return_value.all.return_value = (
        rows
    )

    r = client.get("/api/duplicate-trips?limit=2&offset=0")
    data = r.json()
    assert r.status_code == 200
    assert len(data) == 2
    assert data[0]["count"] == 3


def test_duplicate_trips_empty(client, mock_db):
    mock_db.query.return_value.group_by.return_value.having.return_value.offset.return_value.limit.return_value.all.return_value = (
        []
    )

    r = client.get("/api/duplicate-trips")
    assert r.status_code == 200
    assert r.json() == []


def test_schema(client):
    r = client.get("/api/schema")
    data = r.json()
    assert r.status_code == 200
    assert isinstance(data, list)
    if data:
        assert "name" in data[0]
        assert "type" in data[0]


def test_row_sample_basic(client, mock_db):
    rows = [
        mock_row(id=1, fare_amount=10.0, trip_distance=2.0),
        mock_row(id=2, fare_amount=20.0, trip_distance=3.0),
    ]
    mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = (
        rows
    )

    r = client.get("/api/row-sample?n=2")
    data = r.json()
    assert r.status_code == 200
    assert len(data) == 2
    assert "fare_amount" in data[0]


def test_row_sample_empty(client, mock_db):
    mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = (
        []
    )

    r = client.get("/api/row-sample?n=5")
    assert r.status_code == 200
    assert r.json() == []
