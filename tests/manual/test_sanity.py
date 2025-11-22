"""Manual sanity test - Run against a live server.

This test assumes the server is already running at http://localhost:8000
and requires PostgreSQL and Redis to be available.

To run this test:
1. Start PostgreSQL and Redis
2. Start the server: uvicorn app.main:app --reload
3. Run: pytest tests/manual/test_sanity.py -v -s

This test is skipped by default in automated test runs.
"""
import pytest
import httpx
import asyncio


@pytest.mark.skip(reason="Manual test - requires live server at localhost:8000")
@pytest.mark.asyncio
async def test_full_sanity_check():
    """Complete sanity check of all major functionality."""
    base_url = "http://localhost:8000"
    admin_key = "test-admin-key"  # Use your actual admin key
    
    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        print("\n=== SANITY TEST START ===\n")
        
        # 1. Health check
        print("1. Testing health endpoint...")
        response = await client.get("/health")
        assert response.status_code == 200
        print("   ✓ Health check passed")
        
        # 2. Readiness check
        print("2. Testing readiness endpoint...")
        response = await client.get("/ready")
        assert response.status_code == 200
        print("   ✓ Readiness check passed")
        
        # 3. Create a user
        print("3. Creating test user...")
        username = "sanity_test_user"
        response = await client.post(
            "/admin/users",
            json={"username": username},
            headers={"X-Admin-Key": admin_key}
        )
        assert response.status_code in [201, 409]  # 201 created, 409 if user exists
        print(f"   ✓ User '{username}' created/exists")
        
        # 4. Get user info
        print("4. Getting user info...")
        response = await client.get(
            f"/admin/users/{username}",
            headers={"X-Admin-Key": admin_key}
        )
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["username"] == username
        print(f"   ✓ User info retrieved: block_count={user_data['block_count']}")
        
        # 5. Send a chat message
        print("5. Sending chat message...")
        response = await client.post(
            "/chat",
            json={"username": username, "message": "Hello, this is a sanity test!"}
        )
        assert response.status_code == 200
        chat_data = response.json()
        assert "response" in chat_data
        assert chat_data["violation_detected"] is False
        print(f"   ✓ Chat response received: {chat_data['response'][:50]}...")
        
        # 6. Test content moderation (create victim user)
        print("6. Testing content moderation...")
        victim = "victim_user"
        response = await client.post(
            "/admin/users",
            json={"username": victim},
            headers={"X-Admin-Key": admin_key}
        )
        
        # Send message mentioning victim
        response = await client.post(
            "/chat",
            json={"username": username, "message": f"Hey {victim}, how are you?"}
        )
        assert response.status_code == 200
        chat_data = response.json()
        assert chat_data["violation_detected"] is True
        print(f"   ✓ Violation detected: block_count={chat_data['block_count']}")
        
        # 7. List all users
        print("7. Listing all users...")
        response = await client.get(
            "/admin/users",
            headers={"X-Admin-Key": admin_key}
        )
        assert response.status_code == 200
        response_data = response.json()
        users = response_data["users"]
        assert len(users) >= 2
        print(f"   ✓ Found {len(users)} users in system")
        
        # 8. Test concurrent requests
        print("8. Testing concurrent requests...")
        responses = await asyncio.gather(
            client.post("/chat", json={"username": username, "message": "Concurrent 1"}),
            client.post("/chat", json={"username": username, "message": "Concurrent 2"}),
            return_exceptions=True
        )
        assert all(not isinstance(r, Exception) for r in responses)
        assert all(r.status_code == 200 for r in responses)
        print("   ✓ Concurrent requests handled successfully")
        
        print("\n=== SANITY TEST COMPLETE ===")
        print("✓ All checks passed!")


if __name__ == "__main__":
    # Allow running directly with: python tests/manual/test_sanity.py
    asyncio.run(test_full_sanity_check())
