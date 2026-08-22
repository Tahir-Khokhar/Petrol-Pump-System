import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Return an API client instance."""
    return APIClient()
