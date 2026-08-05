import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.stats import router


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(mock_db):
    with patch("backend.api.stats.get_db", return_value=mock_db):
        app = FastAPI()
        app.include_router(router, prefix="/api")
        return TestClient(app)
