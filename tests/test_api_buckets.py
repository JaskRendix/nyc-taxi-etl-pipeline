from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.buckets import router
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


def call_endpoint(client, path: str, mock_rows):
    with patch("backend.api.buckets.bucket_query", return_value=mock_rows):
        return client.get(path)


def test_fare_buckets_basic(client, mock_db):
    mock_rows = [(1, 10), (2, 5), (3, 2), (4, 1)]
    response = call_endpoint(client, "/api/fare-buckets", mock_rows)
    assert response.status_code == 200
    assert response.json() == [
        {"bucket": "0-10", "count": 10},
        {"bucket": "10-20", "count": 5},
        {"bucket": "20-40", "count": 2},
        {"bucket": "40+", "count": 1},
    ]


def test_fare_buckets_unknown_bucket(client, mock_db):
    mock_rows = [(99, 7)]
    response = call_endpoint(client, "/api/fare-buckets", mock_rows)
    assert response.status_code == 200
    assert response.json() == [{"bucket": "unknown", "count": 7}]


def test_fare_buckets_empty(client, mock_db):
    response = call_endpoint(client, "/api/fare-buckets", [])
    assert response.status_code == 200
    assert response.json() == []


def test_fare_buckets_negative_values(client, mock_db):
    mock_rows = [(-1, 3)]
    response = call_endpoint(client, "/api/fare-buckets", mock_rows)
    assert response.status_code == 200
    assert response.json() == [{"bucket": "unknown", "count": 3}]


def test_fare_buckets_large_values(client, mock_db):
    mock_rows = [(1000000, 42)]
    response = call_endpoint(client, "/api/fare-buckets", mock_rows)
    assert response.status_code == 200
    assert response.json() == [{"bucket": "unknown", "count": 42}]


def test_distance_buckets_basic(client, mock_db):
    mock_rows = [(1, 12), (2, 8), (3, 4), (4, 2)]
    response = call_endpoint(client, "/api/distance-buckets", mock_rows)
    assert response.status_code == 200
    assert response.json() == [
        {"bucket": "0-1", "count": 12},
        {"bucket": "1-3", "count": 8},
        {"bucket": "3-7", "count": 4},
        {"bucket": "7+", "count": 2},
    ]


def test_distance_buckets_unknown_bucket(client, mock_db):
    mock_rows = [(99, 7)]
    response = call_endpoint(client, "/api/distance-buckets", mock_rows)
    assert response.status_code == 200
    assert response.json() == [{"bucket": "unknown", "count": 7}]


def test_distance_buckets_empty(client, mock_db):
    response = call_endpoint(client, "/api/distance-buckets", [])
    assert response.status_code == 200
    assert response.json() == []


def test_distance_buckets_negative_values(client, mock_db):
    mock_rows = [(-1, 3)]
    response = call_endpoint(client, "/api/distance-buckets", mock_rows)
    assert response.status_code == 200
    assert response.json() == [{"bucket": "unknown", "count": 3}]


def test_distance_buckets_large_values(client, mock_db):
    mock_rows = [(1000000, 42)]
    response = call_endpoint(client, "/api/distance-buckets", mock_rows)
    assert response.status_code == 200
    assert response.json() == [{"bucket": "unknown", "count": 42}]
