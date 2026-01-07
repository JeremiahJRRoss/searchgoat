"""Tests for searchgoat.config module."""

import pytest
from pydantic import ValidationError


class TestCriblSettings:
    """Tests for CriblSettings configuration."""
    
    def test_settings_from_env(self, monkeypatch):
        """Settings load from environment variables."""
        monkeypatch.setenv("CRIBL_CLIENT_ID", "env-client-id")
        monkeypatch.setenv("CRIBL_CLIENT_SECRET", "env-secret")
        monkeypatch.setenv("CRIBL_ORG_ID", "env-org")
        monkeypatch.setenv("CRIBL_WORKSPACE", "env-workspace")
        
        from searchgoat.config import CriblSettings
        settings = CriblSettings()
        
        assert settings.client_id == "env-client-id"
        assert settings.org_id == "env-org"
        assert settings.workspace == "env-workspace"
    
    def test_settings_missing_raises_error(self, monkeypatch):
        """Missing required settings raise ValidationError."""
        monkeypatch.delenv("CRIBL_CLIENT_ID", raising=False)
        monkeypatch.delenv("CRIBL_CLIENT_SECRET", raising=False)
        monkeypatch.delenv("CRIBL_ORG_ID", raising=False)
        monkeypatch.delenv("CRIBL_WORKSPACE", raising=False)
        
        from searchgoat.config import CriblSettings
        
        with pytest.raises(ValidationError):
            CriblSettings()
    
    def test_api_base_url_construction(self, monkeypatch):
        """api_base_url is correctly constructed."""
        monkeypatch.setenv("CRIBL_CLIENT_ID", "id")
        monkeypatch.setenv("CRIBL_CLIENT_SECRET", "secret")
        monkeypatch.setenv("CRIBL_ORG_ID", "myorg")
        monkeypatch.setenv("CRIBL_WORKSPACE", "main")
        
        from searchgoat.config import CriblSettings
        settings = CriblSettings()
        
        assert settings.api_base_url == "https://main-myorg.cribl.cloud/api/v1/m/default_search"
    
    def test_auth_url(self, monkeypatch):
        """auth_url returns correct endpoint."""
        monkeypatch.setenv("CRIBL_CLIENT_ID", "id")
        monkeypatch.setenv("CRIBL_CLIENT_SECRET", "secret")
        monkeypatch.setenv("CRIBL_ORG_ID", "org")
        monkeypatch.setenv("CRIBL_WORKSPACE", "ws")
        
        from searchgoat.config import CriblSettings
        settings = CriblSettings()
        
        assert settings.auth_url == "https://login.cribl.cloud/oauth/token"
