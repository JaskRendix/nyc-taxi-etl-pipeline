from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.financial import router
from backend.api.schemas import FarePredictionRequest
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


def mock_mapping(mapping):
    obj = MagicMock()
    obj._mapping = mapping
    return obj


def test_revenue_velocity_basic(client, mock_db):
    rows = [(0, 30.0, 2.0), (1, 40.0, 3.0)]
    mock_db.query.return_value.group_by.return_value.order_by.return_value.all.return_value = (
        rows
    )

    r = client.get("/api/revenue-velocity")
    assert r.status_code == 200
    assert r.json() == [
        {"hour": 0, "avg_earnings_per_hour": 30.0, "avg_earnings_per_mile": 2.0},
        {"hour": 1, "avg_earnings_per_hour": 40.0, "avg_earnings_per_mile": 3.0},
    ]


def test_revenue_velocity_null_values(client, mock_db):
    rows = [(5, None, None)]
    mock_db.query.return_value.group_by.return_value.order_by.return_value.all.return_value = (
        rows
    )

    r = client.get("/api/revenue-velocity")
    assert r.status_code == 200
    assert r.json() == [
        {"hour": 5, "avg_earnings_per_hour": 0.0, "avg_earnings_per_mile": 0.0},
    ]


def test_revenue_velocity_empty(client, mock_db):
    mock_db.query.return_value.group_by.return_value.order_by.return_value.all.return_value = (
        []
    )

    r = client.get("/api/revenue-velocity")
    assert r.status_code == 200
    assert r.json() == []


def test_tolls_and_surcharges_basic(client, mock_db):
    mapping = {
        "total_tolls": 100.0,
        "avg_tolls": 10.0,
        "total_improvement_surcharge": 50.0,
        "avg_improvement_surcharge": 5.0,
        "total_congestion_surcharge": 20.0,
        "avg_congestion_surcharge": 2.0,
    }
    mock_db.query.return_value.one.return_value = mock_mapping(mapping)

    r = client.get("/api/tolls-and-surcharges")
    assert r.status_code == 200
    assert r.json() == {
        "tolls": {"total": 100.0, "average": 10.0},
        "improvement_surcharge": {"total": 50.0, "average": 5.0},
        "congestion_surcharge": {"total": 20.0, "average": 2.0},
    }


def test_tolls_and_surcharges_nulls(client, mock_db):
    mapping = {
        "total_tolls": None,
        "avg_tolls": None,
        "total_improvement_surcharge": None,
        "avg_improvement_surcharge": None,
        "total_congestion_surcharge": None,
        "avg_congestion_surcharge": None,
    }
    mock_db.query.return_value.one.return_value = mock_mapping(mapping)

    r = client.get("/api/tolls-and-surcharges")
    assert r.status_code == 200
    assert r.json() == {
        "tolls": {"total": 0.0, "average": 0.0},
        "improvement_surcharge": {"total": 0.0, "average": 0.0},
        "congestion_surcharge": {"total": 0.0, "average": 0.0},
    }


def test_tax_and_extra_summary_basic(client, mock_db):
    mapping = {
        "total_mta_tax": 30.0,
        "avg_mta_tax": 3.0,
        "total_extra": 40.0,
        "avg_extra": 4.0,
        "total_airport_fee": 50.0,
        "avg_airport_fee": 5.0,
    }
    mock_db.query.return_value.one.return_value = mock_mapping(mapping)

    r = client.get("/api/tax-and-extra-summary")
    assert r.status_code == 200
    assert r.json() == {
        "mta_tax": {"total": 30.0, "average": 3.0},
        "extra": {"total": 40.0, "average": 4.0},
        "airport_fee": {"total": 50.0, "average": 5.0},
    }


def test_tax_and_extra_summary_nulls(client, mock_db):
    mapping = {
        "total_mta_tax": None,
        "avg_mta_tax": None,
        "total_extra": None,
        "avg_extra": None,
        "total_airport_fee": None,
        "avg_airport_fee": None,
    }
    mock_db.query.return_value.one.return_value = mock_mapping(mapping)

    r = client.get("/api/tax-and-extra-summary")
    assert r.status_code == 200
    assert r.json() == {
        "mta_tax": {"total": 0.0, "average": 0.0},
        "extra": {"total": 0.0, "average": 0.0},
        "airport_fee": {"total": 0.0, "average": 0.0},
    }


def test_predict_success(client):
    payload = FarePredictionRequest(
        trip_distance=3.0,
        trip_duration=600,
        hour=14,
        passenger_count=2,
        distance_bucket=1,
        duration_bucket=1,
        speed_mpm=20.0,
        is_peak_hour=False,
        is_airport=False,
    )
    mock_model = MagicMock()
    mock_model.predict.return_value = [12.34]

    with patch("backend.api.financial.load_model", return_value=mock_model):
        # Updated from .dict() to .model_dump() for Pydantic V2 compatibility
        r = client.post("/api/predict", json=payload.model_dump())
        assert r.status_code == 200
        assert r.json() == {"predicted_fare": 12.34}


def test_predict_model_missing(client):
    with patch(
        "backend.api.financial.load_model",
        side_effect=RuntimeError("Model file not found"),
    ):
        r = client.post(
            "/api/predict",
            json={
                "trip_distance": 1,
                "trip_duration": 100,
                "hour": 10,
                "passenger_count": 1,
                "distance_bucket": 1,
                "duration_bucket": 1,
                "speed_mpm": 10,
                "is_peak_hour": False,
                "is_airport": False,
            },
        )
        assert r.status_code == 503
        assert "Model file not found" in r.json()["detail"]


def test_predict_model_failure(client):
    mock_model = MagicMock()
    mock_model.predict.side_effect = Exception("Bad input")

    with patch("backend.api.financial.load_model", return_value=mock_model):
        r = client.post(
            "/api/predict",
            json={
                "trip_distance": 1,
                "trip_duration": 100,
                "hour": 10,
                "passenger_count": 1,
                "distance_bucket": 1,
                "duration_bucket": 1,
                "speed_mpm": 10,
                "is_peak_hour": False,
                "is_airport": False,
            },
        )
        assert r.status_code == 400
        assert "Prediction failed" in r.json()["detail"]
