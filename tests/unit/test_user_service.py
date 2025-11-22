"""Property-based tests for user service."""
import pytest
from hypothesis import given, settings, strategies as st

from app.services.user_service import UserService
from app.services.username_cache import UsernameCache
from app.tests.mocks import InMemoryCache, InMemoryRepository


# Feature: openai-chat-gateway, Property 11: Block count increments by one per request
@given(
    username=st.text(
        min_size=3,
        max_size=50,
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_",
    ),
    initial_count=st.integers(min_value=0, max_value=2),
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.unit
async def test_block_count_increments_by_one(username: str, initial_count: int) -> None:
    """For any chat request with violations, block_count should increase by exactly one."""
    repo = InMemoryRepository()
    cache = InMemoryCache()
    username_cache = UsernameCache(cache, repo)
    user_service = UserService(repo, username_cache)

    await repo.initialize()

    # Create user with initial block count
    user = await repo.create_user(username)
    user.block_count = initial_count
    await repo.update_user(user)

    # Increment block count
    updated_user = await user_service.increment_block_count(username)

    # Should increase by exactly one
    assert updated_user.block_count == initial_count + 1


# Feature: openai-chat-gateway, Property 15: Block count of three triggers blocked status
@given(
    username=st.text(
        min_size=3,
        max_size=50,
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_",
    )
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.unit
async def test_block_count_three_triggers_blocked(username: str) -> None:
    """For any user, when block_count reaches 3, is_blocked should be true."""
    repo = InMemoryRepository()
    cache = InMemoryCache()
    username_cache = UsernameCache(cache, repo)
    user_service = UserService(repo, username_cache)

    await repo.initialize()

    # Create user
    await repo.create_user(username)

    # Increment to 3
    await user_service.increment_block_count(username)
    await user_service.increment_block_count(username)
    final_user = await user_service.increment_block_count(username)

    # Should be blocked
    assert final_user.block_count == 3
    assert final_user.is_blocked is True
    assert await user_service.is_user_blocked(username) is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_or_create_user_creates_new() -> None:
    """get_or_create_user should create user if doesn't exist."""
    repo = InMemoryRepository()
    cache = InMemoryCache()
    username_cache = UsernameCache(cache, repo)
    user_service = UserService(repo, username_cache)

    await repo.initialize()

    user = await user_service.get_or_create_user("alice")

    assert user.username == "alice"
    assert user.block_count == 0
    assert user.is_blocked is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_or_create_user_returns_existing() -> None:
    """get_or_create_user should return existing user if exists."""
    repo = InMemoryRepository()
    cache = InMemoryCache()
    username_cache = UsernameCache(cache, repo)
    user_service = UserService(repo, username_cache)

    await repo.initialize()

    # Create user with some block count
    user1 = await repo.create_user("alice")
    user1.block_count = 2
    await repo.update_user(user1)

    # get_or_create should return existing
    user2 = await user_service.get_or_create_user("alice")

    assert user2.username == "alice"
    assert user2.block_count == 2  # Should preserve existing data
