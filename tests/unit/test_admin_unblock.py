"""Unit tests for admin unblock endpoint."""
import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.api import admin
from app.core.dependencies import get_user_service
from app.models.user import User
from app.services.user_service import UserService
from app.services.username_cache import UsernameCache
from app.tests.mocks import InMemoryRepository, InMemoryCache


@pytest.fixture
def app_with_unblock():
    """Create FastAPI app with admin router."""
    app = FastAPI()
    app.include_router(admin.router)
    
    # Mock admin key
    app.state.admin_key = "test-admin-key"
    
    return app


@pytest.fixture
def mock_user_service():
    """Create mock user service."""
    db = InMemoryRepository()
    cache_client = InMemoryCache()
    username_cache = UsernameCache(cache_client, db)
    return UserService(db, username_cache), db


@pytest.mark.asyncio
async def test_unblock_endpoint_success(app_with_unblock, mock_user_service):
    """Test successful unblock via admin endpoint."""
    service, db = mock_user_service
    
    # Override dependency
    app_with_unblock.dependency_overrides[get_user_service] = lambda: service
    
    # Create blocked user
    user = User(username="blocked_user", block_count=3, is_blocked=True)
    db.users["blocked_user"] = user
    
    async with AsyncClient(app=app_with_unblock, base_url="http://test") as client:
        response = await client.post(
            "/admin/users/blocked_user/unblock",
            headers={"X-Admin-Key": "test-admin-key"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "blocked_user"
    assert data["block_count"] == 0
    assert data["is_blocked"] is False


@pytest.mark.asyncio
async def test_unblock_endpoint_user_not_found(app_with_unblock, mock_user_service):
    """Test unblock endpoint returns 404 for non-existent user."""
    service, db = mock_user_service
    app_with_unblock.dependency_overrides[get_user_service] = lambda: service
    
    async with AsyncClient(app=app_with_unblock, base_url="http://test") as client:
        response = await client.post(
            "/admin/users/nonexistent/unblock",
            headers={"X-Admin-Key": "test-admin-key"}
        )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_unblock_endpoint_user_not_blocked(app_with_unblock, mock_user_service):
    """Test unblock endpoint returns 400 for unblocked user."""
    service, db = mock_user_service
    app_with_unblock.dependency_overrides[get_user_service] = lambda: service
    
    # Create unblocked user
    user = User(username="active_user", block_count=0, is_blocked=False)
    db.users["active_user"] = user
    
    async with AsyncClient(app=app_with_unblock, base_url="http://test") as client:
        response = await client.post(
            "/admin/users/active_user/unblock",
            headers={"X-Admin-Key": "test-admin-key"}
        )
    
    assert response.status_code == 400
    assert "not currently blocked" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_unblock_endpoint_requires_auth(app_with_unblock, mock_user_service):
    """Test unblock endpoint requires admin authentication."""
    service, db = mock_user_service
    app_with_unblock.dependency_overrides[get_user_service] = lambda: service
    
    # Create blocked user
    user = User(username="blocked_user", block_count=3, is_blocked=True)
    db.users["blocked_user"] = user
    
    async with AsyncClient(app=app_with_unblock, base_url="http://test") as client:
        # No auth header
        response = await client.post("/admin/users/blocked_user/unblock")
        assert response.status_code == 422  # Missing required header
        
        # Wrong auth key
        response = await client.post(
            "/admin/users/blocked_user/unblock",
            headers={"X-Admin-Key": "wrong-key"}
        )
        assert response.status_code == 401
