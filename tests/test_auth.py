"""Tests for searchgoat.auth module."""

import pytest
import respx
from httpx import Response

from searchgoat.auth import TokenManager, REFRESH_BUFFER_SECONDS
from searchgoat.exceptions import AuthenticationError


class TestTokenManager:
    """Tests for TokenManager."""
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_get_token_authenticates_on_first_call(self, mock_settings):
        """First call triggers authentication."""
        respx.post("https://login.cribl.cloud/oauth/token").mock(
            return_value=Response(200, json={
                "access_token": "test-token",
                "expires_in": 86400,
            })
        )
        
        import httpx
        manager = TokenManager(mock_settings)
        
        async with httpx.AsyncClient() as client:
            token = await manager.get_token(client)
        
        assert token == "test-token"
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_get_token_caches_token(self, mock_settings):
        """Subsequent calls return cached token."""
        respx.post("https://login.cribl.cloud/oauth/token").mock(
            return_value=Response(200, json={
                "access_token": "cached-token",
                "expires_in": 86400,
            })
        )
        
        import httpx
        manager = TokenManager(mock_settings)
        
        async with httpx.AsyncClient() as client:
            token1 = await manager.get_token(client)
            token2 = await manager.get_token(client)
        
        assert token1 == token2
        assert len(respx.calls) == 1  # Only one auth request
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_get_token_raises_on_401(self, mock_settings):
        """401 response raises AuthenticationError."""
        respx.post("https://login.cribl.cloud/oauth/token").mock(
            return_value=Response(401, json={"error": "invalid_client"})
        )
        
        import httpx
        manager = TokenManager(mock_settings)
        
        with pytest.raises(AuthenticationError):
            async with httpx.AsyncClient() as client:
                await manager.get_token(client)
    
    def test_is_expired_true_when_no_token(self, mock_settings):
        """is_expired returns True when no token exists."""
        manager = TokenManager(mock_settings)
        assert manager.is_expired is True
    
    def test_clear_resets_token(self, mock_settings):
        """clear() resets cached token."""
        manager = TokenManager(mock_settings)
        manager._token = "some-token"
        manager._expires_at = 9999999999
        
        manager.clear()
        
        assert manager._token is None
        assert manager.is_expired is True
