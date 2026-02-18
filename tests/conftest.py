"""Shared test fixtures for the Handwrytten SDK test suite."""

import pytest
import responses

from handwrytten import Handwrytten

TEST_API_KEY = "test_key_abc123"
BASE_URL = "https://api.handwrytten.com/v2/"


@pytest.fixture
def api_key():
    return TEST_API_KEY


@pytest.fixture
def base_url():
    return BASE_URL


@pytest.fixture
def client(api_key, base_url):
    """A Handwrytten client pointed at the real base URL (mocked by responses)."""
    return Handwrytten(api_key=api_key, base_url=base_url, max_retries=1)


@pytest.fixture
def mock_api():
    """Activate the `responses` mock and yield the RequestsMock for adding routes."""
    with responses.RequestsMock() as rsps:
        yield rsps
