"""Shared test fixtures for searchgoat tests."""

import pytest


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    from unittest.mock import MagicMock, PropertyMock
    
    # Create a proper mock for SecretStr
    mock_secret = MagicMock()
    mock_secret.get_secret_value.return_value = "test-secret"
    
    settings = MagicMock()
    settings.client_id = "test-client-id"
    settings.client_secret = mock_secret
    settings.org_id = "test-org"
    settings.workspace = "test-workspace"
    settings.auth_url = "https://login.cribl.cloud/oauth/token"
    settings.api_base_url = "https://test-workspace-test-org.cribl.cloud/api/v1/m/default_search"
    
    return settings


@pytest.fixture
def base_url():
    """Base URL for mocked API."""
    return "https://test-workspace-test-org.cribl.cloud/api/v1/m/default_search"
