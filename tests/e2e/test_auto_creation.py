"""E2E tests for auto-creation feature."""
import pytest
import httpx


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_auto_create_user_on_first_chat(e2e_client: httpx.AsyncClient):
    """Test that AUTO_CREATE_USERS=true creates user on first chat request."""
    # Use a unique username for this test
    username = "e2e_auto_user_001"
    
    # Verify user doesn't exist yet
    response = await e2e_client.get(
        f"/admin/users/{username}",
        headers={"X-Admin-Key": "test-admin-key"}
    )
    assert response.status_code == 404
    
    # Send chat request (should auto-create user)
    response = await e2e_client.post(
        "/chat",
        json={"username": username, "message": "Hello!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["block_count"] == 0
    assert data["violation_detected"] is False
    
    # Verify user was created
    response = await e2e_client.get(
        f"/admin/users/{username}",
        headers={"X-Admin-Key": "test-admin-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == username
    assert data["block_count"] == 0
    assert data["is_blocked"] is False


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_existing_user_not_recreated(e2e_client: httpx.AsyncClient):
    """Test that existing users are not recreated on chat."""
    username = "e2e_existing_user_001"
    
    # Create user via admin endpoint
    response = await e2e_client.post(
        "/admin/users",
        json={"username": username},
        headers={"X-Admin-Key": "test-admin-key"}
    )
    assert response.status_code == 201
    
    # Send chat request (should use existing user)
    response = await e2e_client.post(
        "/chat",
        json={"username": username, "message": "Hello!"}
    )
    assert response.status_code == 200
    
    # Verify user still exists with same data
    response = await e2e_client.get(
        f"/admin/users/{username}",
        headers={"X-Admin-Key": "test-admin-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == username
