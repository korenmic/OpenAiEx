"""Unit test configuration and fixtures."""
import os
import pytest
from unittest.mock import Mock

# Set required environment variables for testing
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("ADMIN_API_KEY", "test-admin-key")
os.environ.setdefault("DATABASE_URL", "postgresql://localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Reset settings cache between tests."""
    import app.core.config as config_module
    
    # Clear the global settings instance
    config_module._settings = None
    yield
    config_module._settings = None
