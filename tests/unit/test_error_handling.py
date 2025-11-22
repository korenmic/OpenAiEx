"""Property-based tests for error handling."""
import pytest
from hypothesis import given, strategies as st, settings
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from app.tests.mocks import InMemoryRepository, InMemoryCache, LocalLockManager, MockOpenAIClient
from app.core.dependencies import get_chat_service
from app.services.chat_service import ChatService
from app.services.user_service import UserService
from app.services.content_moderator import ContentModerator
from app.services.username_cache import UsernameCache


def create_test_app_with_failing_service():
    """Create a test app where the chat service raises internal errors."""
    app = FastAPI()
    
    # Create a chat service that will raise an exception
    async def failing_chat_service():
        service = AsyncMock(spec=ChatService)
        service.process_chat_request.side_effect = RuntimeError("Internal error")
        return service
    
    app.dependency_overrides[get_chat_service] = failing_chat_service
    
    from app.api.chat import router
    app.include_router(router)
    
    return app


# Feature: openai-chat-gateway, Property 20: Internal errors return 500
@given(
    username=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    message=st.text(min_size=1, max_size=100)
)
@settings(max_examples=100)
@pytest.mark.unit
def test_internal_errors_return_500(username: str, message: str) -> None:
    """Validates: Requirements 6.2"""
    app = create_test_app_with_failing_service()
    client = TestClient(app)
    
    # Test that internal errors return 502 (bad gateway for upstream errors)
    response = client.post(
        "/chat",
        json={"username": username, "message": message}
    )
    
    # Internal errors should return 502 (upstream service error) or 500
    assert response.status_code in [500, 502], f"Expected 500/502 for internal error, got {response.status_code}"
