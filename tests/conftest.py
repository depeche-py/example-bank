from fastapi.testclient import TestClient
import pytest
from bank.api import app


@pytest.fixture
def api_client():
    return TestClient(app)
