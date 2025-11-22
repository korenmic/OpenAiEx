"""Property-based tests for admin endpoints."""
import pytest
from hypothesis import given, strategies as st, settings
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.tests.mocks import InMemoryRepository, InMemoryCache
from app.core.dependencies import get_user_service
from app.services.user_service import UserService
from app.services.username_cache import UsernameCache


def create_test_app():
    """Create a test FastAPI app with mocked dependencies and fresh state."""
    app = FastAPI()
    
    db = InMemoryRepository()
    cache = InMemoryCache()
    username_cache = UsernameCache(cache, db)
    user_service = UserService(db, username_cache)
    
    async def override_user_service():
        return user_service
    
    app.dependency_overrides[get_user_service] = override_user_service
    
    # Import and include router
    from app.api.admin import router
    app.include_router(router)
    
    return app, db


# Feature: openai-chat-gateway, Property 17: Correct HTTP status codes for success
@given(username=st.text(min_size=1, max_size=50, alphabet=st.characters(
    min_codepoint=97, max_codepoint=122  # a-z only
)))
@settings(max_examples=100, deadline=None)
@pytest.mark.unit
def test_correct_status_codes_for_success(username: str) -> None:
    """Validates: Requirements 5.1, 5.2, 5.3"""
    app, db = create_test_app()
    client = TestClient(app)
    
    # Test POST /admin/users returns 201
    response = client.post(
        "/admin/users",
        json={"username": username},
        headers={"X-Admin-Key": "test-admin-key"}
    )
    assert response.status_code == 201, f"Expected 201 for user creation, got {response.status_code}"
    
    # Test GET /admin/users/{username} returns 200
    response = client.get(
        f"/admin/users/{username}",
        headers={"X-Admin-Key": "test-admin-key"}
    )
    assert response.status_code == 200, f"Expected 200 for user retrieval, got {response.status_code}"
    
    # Test GET /admin/users returns 200
    response = client.get(
        "/admin/users",
        headers={"X-Admin-Key": "test-admin-key"}
    )
    assert response.status_code == 200, f"Expected 200 for list users, got {response.status_code}"






# Feature: openai-chat-gateway, Property 18: 404 for non-existent resources
@given(username=st.text(min_size=1, max_size=50, alphabet=st.characters(
    min_codepoint=97, max_codepoint=122  # a-z only
)))
@settings(max_examples=100, deadline=None)
@pytest.mark.unit
def test_404_for_nonexistent_resources(username: str) -> None:
    """Validates: Requirements 5.4"""
    app, db = create_test_app()
    client = TestClient(app)
    
    # Test GET for non-existent user returns 404
    response = client.get(
        f"/admin/users/{username}",
        headers={"X-Admin-Key": "test-admin-key"}
    )
    assert response.status_code == 404, f"Expected 404 for non-existent user, got {response.status_code}"
    assert "not found" in response.json()["detail"].lower()


# Feature: openai-chat-gateway, Property 19: 400 for invalid input
@given(username=st.text(max_size=0))  # Empty username
@settings(max_examples=100)
@pytest.mark.unit
def test_400_for_invalid_input(username: str) -> None:
    """Validates: Requirements 5.5, 6.4"""
    app, db = create_test_app()
    client = TestClient(app)
    
    # Test POST with empty username returns 400 or 422 (validation error)
    response = client.post(
        "/admin/users",
        json={"username": username},
        headers={"X-Admin-Key": "test-admin-key"}
    )
    assert response.status_code in [400, 422], f"Expected 400/422 for invalid input, got {response.status_code}"
