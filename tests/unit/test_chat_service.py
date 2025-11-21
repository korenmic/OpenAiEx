"""Property-based tests for chat service."""
import pytest

from app.services.chat_service import ChatService
from app.services.content_moderator import ContentModerator
from app.services.user_service import UserService
from app.services.username_cache import UsernameCache
from app.tests.mocks import InMemoryCache, InMemoryRepository, LocalLockManager, MockOpenAIClient


# Feature: openai-chat-gateway, Property 6: Non-blocked users can make chat requests
@pytest.mark.asyncio
@pytest.mark.unit
async def test_non_blocked_users_can_chat() -> None:
    """For any non-blocked user, chat request should succeed."""
    repo = InMemoryRepository()
    cache = InMemoryCache()
    username_cache = UsernameCache(cache, repo)
    user_service = UserService(repo, username_cache)
    content_moderator = ContentModerator(username_cache)
    openai_client = MockOpenAIClient()
    lock_manager = LocalLockManager()
    chat_service = ChatService(user_service, content_moderator, openai_client, lock_manager)

    await repo.initialize()
    await repo.create_user("alice")

    response = await chat_service.process_chat_request("alice", "Hello")

    assert response.response == "This is a mock response from OpenAI."
    assert response.block_count == 0
    assert response.violation_detected is False


# Feature: openai-chat-gateway, Property 7: Blocked users are rejected
@pytest.mark.asyncio
@pytest.mark.unit
async def test_blocked_users_rejected() -> None:
    """For any blocked user, chat request should be rejected."""
    repo = InMemoryRepository()
    cache = InMemoryCache()
    username_cache = UsernameCache(cache, repo)
    user_service = UserService(repo, username_cache)
    content_moderator = ContentModerator(username_cache)
    openai_client = MockOpenAIClient()
    lock_manager = LocalLockManager()
    chat_service = ChatService(user_service, content_moderator, openai_client, lock_manager)

    await repo.initialize()
    user = await repo.create_user("alice")
    user.is_blocked = True
    await repo.update_user(user)

    with pytest.raises(PermissionError, match="blocked"):
        await chat_service.process_chat_request("alice", "Hello")


# Feature: openai-chat-gateway, Property 12: Violations don't prevent request processing
@pytest.mark.asyncio
@pytest.mark.unit
async def test_violations_dont_prevent_processing() -> None:
    """For any chat with violations, request should still process."""
    repo = InMemoryRepository()
    cache = InMemoryCache()
    username_cache = UsernameCache(cache, repo)
    user_service = UserService(repo, username_cache)
    content_moderator = ContentModerator(username_cache)
    openai_client = MockOpenAIClient()
    lock_manager = LocalLockManager()
    chat_service = ChatService(user_service, content_moderator, openai_client, lock_manager)

    await repo.initialize()
    await repo.create_user("alice")
    await repo.create_user("bob")

    # Message mentions bob
    response = await chat_service.process_chat_request("alice", "Hello bob")

    # Should still get response
    assert response.response == "This is a mock response from OpenAI."
    assert response.block_count == 1  # Incremented
    assert response.violation_detected is True


# Feature: openai-chat-gateway, Property 16: Third violation request completes before blocking
@pytest.mark.asyncio
@pytest.mark.unit
async def test_third_violation_completes_then_blocks() -> None:
    """For user with 2 violations, 3rd violation request completes, 4th is blocked."""
    repo = InMemoryRepository()
    cache = InMemoryCache()
    username_cache = UsernameCache(cache, repo)
    user_service = UserService(repo, username_cache)
    content_moderator = ContentModerator(username_cache)
    openai_client = MockOpenAIClient()
    lock_manager = LocalLockManager()
    chat_service = ChatService(user_service, content_moderator, openai_client, lock_manager)

    await repo.initialize()
    user = await repo.create_user("alice")
    user.block_count = 2
    await repo.update_user(user)
    await repo.create_user("bob")

    # 3rd violation - should complete
    response = await chat_service.process_chat_request("alice", "Hello bob")
    assert response.response == "This is a mock response from OpenAI."
    assert response.block_count == 3

    # 4th request - should be blocked
    with pytest.raises(PermissionError, match="blocked"):
        await chat_service.process_chat_request("alice", "Another message")


# Feature: openai-chat-gateway, Property 9: OpenAI errors are propagated
@pytest.mark.asyncio
@pytest.mark.unit
async def test_openai_errors_propagated() -> None:
    """For any OpenAI error, it should be propagated to user."""
    from app.services.openai_client import OpenAIServiceError

    repo = InMemoryRepository()
    cache = InMemoryCache()
    username_cache = UsernameCache(cache, repo)
    user_service = UserService(repo, username_cache)
    content_moderator = ContentModerator(username_cache)

    # Mock client that raises error
    class ErrorOpenAIClient:
        async def send_chat_request(self, message: str) -> str:
            raise OpenAIServiceError("OpenAI API error: 500")

    openai_client = ErrorOpenAIClient()
    lock_manager = LocalLockManager()
    chat_service = ChatService(user_service, content_moderator, openai_client, lock_manager)

    await repo.initialize()
    await repo.create_user("alice")

    with pytest.raises(OpenAIServiceError, match="OpenAI API error"):
        await chat_service.process_chat_request("alice", "Hello")
