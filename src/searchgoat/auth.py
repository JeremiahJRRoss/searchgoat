"""OAuth2 authentication for Cribl Cloud."""

import time
from typing import Optional

import httpx

from searchgoat.config import CriblSettings
from searchgoat.exceptions import AuthenticationError


# Refresh token 5 minutes before expiry
REFRESH_BUFFER_SECONDS = 300


class TokenManager:
    """
    Manages OAuth2 tokens for Cribl Cloud API.
    
    Handles token acquisition and automatic refresh before expiry.
    Thread-safe for use with async HTTP clients.
    """
    
    def __init__(self, settings: CriblSettings):
        """
        Initialize token manager.
        
        Args:
            settings: Cribl configuration with credentials
        """
        self._settings = settings
        self._token: Optional[str] = None
        self._expires_at: float = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if current token is expired or about to expire."""
        return time.time() >= (self._expires_at - REFRESH_BUFFER_SECONDS)
    
    async def get_token(self, client: httpx.AsyncClient) -> str:
        """
        Get a valid access token, refreshing if necessary.
        
        Args:
            client: HTTP client to use for token request
            
        Returns:
            Valid access token
            
        Raises:
            AuthenticationError: If authentication fails
        """
        if self._token is None or self.is_expired:
            await self._authenticate(client)
        
        return self._token  # type: ignore
    
    async def _authenticate(self, client: httpx.AsyncClient) -> None:
        """
        Perform OAuth2 client_credentials flow.
        
        Args:
            client: HTTP client to use for token request
            
        Raises:
            AuthenticationError: If authentication fails
        """
        payload = {
            "grant_type": "client_credentials",
            "client_id": self._settings.client_id,
            "client_secret": self._settings.client_secret.get_secret_value(),
            "audience": "https://api.cribl.cloud",
        }
        
        try:
            response = await client.post(
                self._settings.auth_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise AuthenticationError(
                f"Authentication failed: {e.response.status_code} - {e.response.text}"
            ) from e
        except httpx.ConnectError as e:
            raise AuthenticationError(f"Could not connect to auth server: {e}") from e
        
        data = response.json()
        self._token = data["access_token"]
        self._expires_at = time.time() + data.get("expires_in", 86400)
    
    def clear(self) -> None:
        """Clear cached token, forcing re-authentication on next request."""
        self._token = None
        self._expires_at = 0
