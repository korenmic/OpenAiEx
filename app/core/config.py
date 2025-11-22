"""Configuration management using pydantic-settings."""
import hashlib
import secrets
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Required
    openai_api_key: str

    # Optional with defaults
    openai_model: Optional[str] = None  # Auto-selected if not provided
    model_preference: str = "CHEAPEST"  # FASTEST or CHEAPEST
    database_url: str = "postgresql+asyncpg://localhost:5432/gateway"
    redis_url: str = "redis://localhost:6379"
    auto_create_users: bool = True
    admin_api_key: Optional[str] = None

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def get_or_generate_admin_key(self) -> str:
        """Get admin key from env or generate and save to file."""
        if self.admin_api_key:
            return self.admin_api_key

        # Generate random admin key
        key = hashlib.sha256(secrets.token_bytes(32)).hexdigest()

        # Save to file
        key_file = Path.home() / ".gateway_admin_key"
        key_file.write_text(key)
        key_file.chmod(0o600)  # Read/write for owner only

        print(f"Generated admin API key and saved to: {key_file}")
        return key


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore
    return _settings
