"""Unit tests for automatic time-based unblocking."""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from app.models.user import User
from app.services.chat_service import ChatService
from app.services.content_moderator import ContentModerator
from app.services.user_service import UserService
from app.services.username_cache import UsernameCache
from app.tests.mocks import InMemoryRepository, InMemoryCache, MockOpenAIClient, LocalLockManager


@pytest.fixture
def chat_service_with_mocks():
    """Create chat service with all mocks."""
    db = InMemoryRepository()
    cache_client = InMemoryCache()
    username_cache = UsernameCache(cache_client, db)
    user_service = UserService(db, username_cache)
    content_moderator = ContentModerator(username_cache)
    openai_client = MockOpenAIClient()
    lock_manager = LocalLockManager()
    
    chat_service = ChatService(user_service, content_moderator, openai_client, lock_manager)
    
    return chat_service, db, user_service


@pytest.mark.asyncio
async def test_auto_unblock_expired_user(chat_service_with_mocks):
    """Test that user blocked longer than BLOCK_DURATION_HOURS is automatically unblocked."""
    chat_service, db, user_service = chat_service_with_mocks
    
    # Create user blocked 25 hours ago (default duration is 24 hours)
    blocked_time = datetime.now(timezone.utc) - timedelta(hours=25)
    user = User(username="expired_block", block_count=3, is_blocked=True, blocked_at=blocked_time)
    db.users["expired_block"] = user
    
    # Process chat request - should auto-unblock
    response = await chat_service.process_chat_request("expired_block", "Hello")
    
    # Verify user was unblocked
    updated_user = await user_service.get_user("expired_block")
    assert updated_user.is_blocked is False
    assert updated_user.block_count == 0
    assert updated_user.blocked_at is None
    assert response.response == "This is a mock response from OpenAI."


@pytest.mark.asyncio
async def test_no_auto_unblock_within_duration(chat_service_with_mocks):
    """Test that user blocked less than BLOCK_DURATION_HOURS remains blocked."""
    chat_service, db, user_service = chat_service_with_mocks
    
    # Create user blocked 1 hour ago (within 24 hour duration)
    blocked_time = datetime.now(timezone.utc) - timedelta(hours=1)
    user = User(username="recent_block", block_count=3, is_blocked=True, blocked_at=blocked_time)
    db.users["recent_block"] = user
    
    # Process chat request - should remain blocked
    with pytest.raises(PermissionError, match="blocked and cannot make requests"):
        await chat_service.process_chat_request("recent_block", "Hello")
    
    # Verify user still blocked
    updated_user = await user_service.get_user("recent_block")
    assert updated_user.is_blocked is True
    assert updated_user.block_count == 3


@pytest.mark.asyncio
async def test_auto_unblock_exactly_at_expiry(chat_service_with_mocks):
    """Test that user blocked exactly BLOCK_DURATION_HOURS is unblocked."""
    chat_service, db, user_service = chat_service_with_mocks
    
    # Create user blocked exactly 24 hours ago
    blocked_time = datetime.now(timezone.utc) - timedelta(hours=24)
    user = User(username="exact_expiry", block_count=3, is_blocked=True, blocked_at=blocked_time)
    db.users["exact_expiry"] = user
    
    # Process chat request - should auto-unblock
    response = await chat_service.process_chat_request("exact_expiry", "Hello")
    
    # Verify user was unblocked
    updated_user = await user_service.get_user("exact_expiry")
    assert updated_user.is_blocked is False
    assert updated_user.block_count == 0


@pytest.mark.asyncio
async def test_blocked_at_set_when_user_blocked(chat_service_with_mocks):
    """Test that blocked_at is set when user reaches 3 violations."""
    chat_service, db, user_service = chat_service_with_mocks
    
    # Create user with 2 violations
    user = User(username="test_user", block_count=2, is_blocked=False)
    db.users["test_user"] = user
    
    # Create another user to trigger violation
    victim = User(username="victim", block_count=0, is_blocked=False)
    db.users["victim"] = user
    
    # Send message mentioning victim (triggers violation)
    before_time = datetime.now(timezone.utc)
    response = await chat_service.process_chat_request("test_user", "Hey victim, how are you?")
    after_time = datetime.now(timezone.utc)
    
    # Verify user is blocked with timestamp
    updated_user = await user_service.get_user("test_user")
    assert updated_user.is_blocked is True
    assert updated_user.block_count == 3
    assert updated_user.blocked_at is not None
    assert before_time <= updated_user.blocked_at <= after_time


@pytest.mark.asyncio
async def test_blocked_at_cleared_on_manual_unblock(chat_service_with_mocks):
    """Test that blocked_at is cleared when user is manually unblocked."""
    chat_service, db, user_service = chat_service_with_mocks
    
    # Create blocked user with timestamp
    blocked_time = datetime.now(timezone.utc) - timedelta(hours=1)
    user = User(username="manual_unblock", block_count=3, is_blocked=True, blocked_at=blocked_time)
    db.users["manual_unblock"] = user
    
    # Manually unblock
    unblocked_user = await user_service.unblock_user("manual_unblock")
    
    # Verify blocked_at is cleared
    assert unblocked_user.blocked_at is None
    assert unblocked_user.is_blocked is False
    assert unblocked_user.block_count == 0


@pytest.mark.asyncio
async def test_legacy_blocked_user_without_timestamp(chat_service_with_mocks):
    """Test that blocked user without blocked_at timestamp remains blocked."""
    chat_service, db, user_service = chat_service_with_mocks
    
    # Create blocked user without timestamp (legacy data)
    user = User(username="legacy_block", block_count=3, is_blocked=True, blocked_at=None)
    db.users["legacy_block"] = user
    
    # Process chat request - should remain blocked
    with pytest.raises(PermissionError, match="blocked and cannot make requests"):
        await chat_service.process_chat_request("legacy_block", "Hello")
    
    # Verify user still blocked
    updated_user = await user_service.get_user("legacy_block")
    assert updated_user.is_blocked is True


@pytest.mark.asyncio
@patch('app.core.config.get_settings')
async def test_custom_block_duration(mock_settings, chat_service_with_mocks):
    """Test that custom BLOCK_DURATION_HOURS is respected."""
    chat_service, db, user_service = chat_service_with_mocks
    
    # Mock settings with custom duration (48 hours)
    from app.core.config import Settings
    custom_settings = Settings(
        openai_api_key="test-key",
        block_duration_hours=48
    )
    mock_settings.return_value = custom_settings
    chat_service.settings = custom_settings
    
    # Create user blocked 25 hours ago (within 48 hour duration)
    blocked_time = datetime.now(timezone.utc) - timedelta(hours=25)
    user = User(username="custom_duration", block_count=3, is_blocked=True, blocked_at=blocked_time)
    db.users["custom_duration"] = user
    
    # Process chat request - should remain blocked (25 < 48)
    with pytest.raises(PermissionError, match="blocked and cannot make requests"):
        await chat_service.process_chat_request("custom_duration", "Hello")
