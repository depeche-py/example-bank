import pytest
from fastapi.testclient import TestClient

from bank.api import app


@pytest.fixture
def api_client():
    return TestClient(app)
