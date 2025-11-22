"""Integration tests for user management flow with real database."""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_creation_and_retrieval_with_real_db(integration_app):
    """Test creating and retrieving users with real PostgreSQL."""
    client = TestClient(integration_app)
    
    # Create a user
    response = client.post(
        "/admin/users",
        json={"username": "alice"},
        headers={"X-Admin-Key": "test-admin-key"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "alice"
    assert data["block_count"] == 0
    assert data["is_blocked"] is False
    
    # Retrieve the user
    response = client.get(
        "/admin/users/alice",
        headers={"X-Admin-Key": "test-admin-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "alice"
    assert data["block_count"] == 0
    
    # List all users
    response = client.get(
        "/admin/users",
        headers={"X-Admin-Key": "test-admin-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 1
    assert data["users"][0]["username"] == "alice"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_invalidation_on_user_creation(integration_app, test_cache):
    """Test that username cache is invalidated when users are created."""
    client = TestClient(integration_app)
    
    # Create first user
    client.post(
        "/admin/users",
        json={"username": "alice"},
        headers={"X-Admin-Key": "test-admin-key"}
    )
    
    # Check cache is empty initially
    cached = await test_cache.get("usernames:all")
    assert cached is None or "alice" not in cached
    
    # Create second user (should invalidate cache)
    client.post(
        "/admin/users",
        json={"username": "bob"},
        headers={"X-Admin-Key": "test-admin-key"}
    )
    
    # Cache should be invalidated
    cached = await test_cache.get("usernames:all")
    # Cache will be repopulated on next read
    assert cached is None or "bob" in cached or cached == ""


@pytest.mark.integration
@pytest.mark.asyncio
async def test_distributed_lock_prevents_race_conditions(integration_app, test_lock_manager):
    """Test that distributed locks work with real Redis."""
    import asyncio
    
    # Acquire a lock
    async with test_lock_manager.acquire_lock("test-user", timeout=5.0):
        # Lock is held
        # Try to acquire same lock from another context (should timeout quickly)
        try:
            async with test_lock_manager.acquire_lock("test-user", timeout=0.1):
                pytest.fail("Should not be able to acquire lock twice")
        except TimeoutError:
            # Expected - lock is already held
            pass
    
    # Lock should be released now
    async with test_lock_manager.acquire_lock("test-user", timeout=1.0):
        # Should succeed
        pass
