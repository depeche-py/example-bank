import pytest
from fastapi.testclient import TestClient

from bank.api import app


@pytest.fixture
def api_client():
    return TestClient(app)


@pytest.fixture
def run_background_processing():
    from bank.infra import get_runnables

    def inner(rounds: int = 1):
        for _ in range(rounds):
            for runnable in get_runnables():
                runnable.run()

    return inner
