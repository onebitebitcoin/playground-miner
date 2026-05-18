import pytest
from django.test import Client


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def api_client():
    """Django test client pre-configured for JSON API calls."""
    c = Client()
    c.defaults['content_type'] = 'application/json'
    return c
