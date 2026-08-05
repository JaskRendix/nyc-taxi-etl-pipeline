from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.health import router
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


def test_health_ok(client, mock_db):
    mock_db.query.return_value.scalar.return_value = 123

    r = client.get("/api/health")
    data = r.json()
    assert r.status_code == 200
    assert data["status"] == "ok"
    assert data["db"] == "connected"
    assert data["rows"] == 123


def test_health_error(client, mock_db):
    mock_db.query.side_effect = Exception("DB down")

    r = client.get("/api/health")
    data = r.json()
    assert r.status_code == 200
    assert data["status"] == "error"
    assert data["db"] == "unreachable"
    assert data["rows"] is None
