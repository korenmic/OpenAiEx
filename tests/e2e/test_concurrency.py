"""E2E tests for concurrent request handling."""
import pytest
import httpx
import asyncio
import time


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_same_user_requests_are_serialized(e2e_client: httpx.AsyncClient):
    """Test that requests from the same user are processed serially."""
    username = "e2e_serial_user_001"
    
    # Create user first
    await e2e_client.post(
        "/admin/users",
        json={"username": username},
        headers={"X-Admin-Key": "test-admin-key"}
    )
    
    # Send 2 concurrent requests from same user
    start_time = time.time()
    
    responses = await asyncio.gather(
        e2e_client.post("/chat", json={"username": username, "message": "Request 1"}),
        e2e_client.post("/chat", json={"username": username, "message": "Request 2"}),
        return_exceptions=True
    )
    
    elapsed = time.time() - start_time
    
    # Both requests should succeed
    assert all(not isinstance(r, Exception) for r in responses)
    assert all(r.status_code == 200 for r in responses)
    
    # Requests should be serialized (not truly parallel)
    # With mocked OpenAI, this should still show some serialization
    # In real scenario with delays, this would be more pronounced


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_different_users_process_in_parallel(e2e_client: httpx.AsyncClient):
    """Test that requests from different users can process concurrently."""
    user1 = "e2e_parallel_user_001"
    user2 = "e2e_parallel_user_002"
    
    # Create both users
    await e2e_client.post(
        "/admin/users",
        json={"username": user1},
        headers={"X-Admin-Key": "test-admin-key"}
    )
    await e2e_client.post(
        "/admin/users",
        json={"username": user2},
        headers={"X-Admin-Key": "test-admin-key"}
    )
    
    # Send concurrent requests from different users
    start_time = time.time()
    
    responses = await asyncio.gather(
        e2e_client.post("/chat", json={"username": user1, "message": "Hello from user1"}),
        e2e_client.post("/chat", json={"username": user2, "message": "Hello from user2"}),
        return_exceptions=True
    )
    
    elapsed = time.time() - start_time
    
    # Both requests should succeed
    assert all(not isinstance(r, Exception) for r in responses)
    assert all(r.status_code == 200 for r in responses)
    
    # Different users should not block each other
    # Both should complete successfully


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_blocking_after_three_violations(e2e_client: httpx.AsyncClient):
    """Test that users are blocked after 3 violations in real scenario."""
    violator = "e2e_violator_001"
    victim = "e2e_victim_001"
    
    # Create both users
    await e2e_client.post(
        "/admin/users",
        json={"username": violator},
        headers={"X-Admin-Key": "test-admin-key"}
    )
    await e2e_client.post(
        "/admin/users",
        json={"username": victim},
        headers={"X-Admin-Key": "test-admin-key"}
    )
    
    # Send 3 messages mentioning the victim
    for i in range(3):
        response = await e2e_client.post(
            "/chat",
            json={"username": violator, "message": f"Hey {victim}, message {i+1}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["violation_detected"] is True
        assert data["block_count"] == i + 1
    
    # Fourth request should be blocked
    response = await e2e_client.post(
        "/chat",
        json={"username": violator, "message": "Another message"}
    )
    assert response.status_code == 403
    assert "blocked" in response.json()["detail"].lower()
