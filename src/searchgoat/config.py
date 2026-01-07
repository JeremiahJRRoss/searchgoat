"""Configuration management using pydantic-settings."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class CriblSettings(BaseSettings):
    """
    Cribl Search API configuration.
    
    Loads from environment variables or .env file:
    - CRIBL_CLIENT_ID
    - CRIBL_CLIENT_SECRET
    - CRIBL_ORG_ID
    - CRIBL_WORKSPACE
    
    Example .env file:
        CRIBL_CLIENT_ID=your-client-id
        CRIBL_CLIENT_SECRET=your-client-secret
        CRIBL_ORG_ID=your-org-id
        CRIBL_WORKSPACE=main
    """
    
    model_config = SettingsConfigDict(
        env_prefix="CRIBL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    client_id: str
    client_secret: SecretStr
    org_id: str
    workspace: str
    
    @property
    def auth_url(self) -> str:
        """OAuth2 token endpoint."""
        return "https://login.cribl.cloud/oauth/token"
    
    @property
    def api_base_url(self) -> str:
        """Construct the API base URL from workspace and org_id."""
        return f"https://{self.workspace}-{self.org_id}.cribl.cloud/api/v1/m/default_search"
