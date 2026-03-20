from fastapi.testclient import TestClient
import pytest

import main


@pytest.fixture
def client() -> TestClient:
    return TestClient(main.app)
