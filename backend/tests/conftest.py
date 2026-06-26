"""Backend test configuration."""

import pytest
from fastapi.testclient import TestClient

from novo.core.config import get_settings
from novo.main import create_app


@pytest.fixture
def client() -> TestClient:
    get_settings.cache_clear()
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()
