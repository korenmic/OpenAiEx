"""Unit tests for admin authentication."""
import pytest
from fastapi import HTTPException

from app.api.auth import verify_admin_key


@pytest.mark.asyncio
@pytest.mark.unit
async def test_valid_admin_key() -> None:
    """Valid admin key should pass authentication."""
    from app.core.config import get_settings

    settings = get_settings()
    admin_key = settings.get_or_generate_admin_key()

    result = await verify_admin_key(admin_key)
    assert result == admin_key


@pytest.mark.asyncio
@pytest.mark.unit
async def test_invalid_admin_key() -> None:
    """Invalid admin key should raise 401."""
    with pytest.raises(HTTPException) as exc_info:
        await verify_admin_key("invalid-key")

    assert exc_info.value.status_code == 401
    assert "Invalid admin API key" in exc_info.value.detail


@pytest.mark.asyncio
@pytest.mark.unit
async def test_missing_admin_key() -> None:
    """Missing admin key should raise exception."""
    # Header(...) makes it required, so FastAPI will handle this
    # This test verifies our function behavior when called directly
    with pytest.raises(HTTPException) as exc_info:
        await verify_admin_key("")

    assert exc_info.value.status_code == 401
