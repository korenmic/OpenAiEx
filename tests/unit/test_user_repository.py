"""Property-based tests for user repository."""
import pytest
from hypothesis import given, settings, strategies as st

from app.tests.mocks import InMemoryRepository


# Feature: openai-chat-gateway, Property 1: User creation initializes block count to zero
@given(
    username=st.text(
        min_size=3,
        max_size=50,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"
        ),
    )
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.unit
async def test_user_creation_initializes_block_count(username: str) -> None:
    """For any valid username, creating a new user should result in block_count=0 and is_blocked=false."""
    repo = InMemoryRepository()
    await repo.initialize()

    user = await repo.create_user(username)

    assert user.block_count == 0
    assert user.is_blocked is False
    assert user.username == username


# Feature: openai-chat-gateway, Property 2: User data retrieval accuracy
@given(
    username=st.text(
        min_size=3,
        max_size=50,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"
        ),
    ),
    block_count=st.integers(min_value=0, max_value=3),
    is_blocked=st.booleans(),
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.unit
async def test_user_data_retrieval_accuracy(
    username: str, block_count: int, is_blocked: bool
) -> None:
    """For any user in the system, retrieving that user's information should return exact data."""
    repo = InMemoryRepository()
    await repo.initialize()

    # Create user with specific values
    user = await repo.create_user(username)
    user.block_count = block_count
    user.is_blocked = is_blocked
    await repo.update_user(user)

    # Retrieve and verify
    retrieved = await repo.get_user(username)

    assert retrieved is not None
    assert retrieved.username == username
    assert retrieved.block_count == block_count
    assert retrieved.is_blocked == is_blocked


# Feature: openai-chat-gateway, Property 3: List all users completeness
@given(
    usernames=st.lists(
        st.text(
            min_size=3,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"
            ),
        ),
        min_size=1,
        max_size=10,
        unique=True,
    )
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_all_users_completeness(usernames: list[str]) -> None:
    """For any set of users created, list users should return all users with complete data."""
    repo = InMemoryRepository()
    await repo.initialize()

    # Create all users
    created_users = []
    for username in usernames:
        user = await repo.create_user(username)
        created_users.append(user)

    # List all users
    all_users = await repo.get_all_users()

    # Verify completeness
    assert len(all_users) == len(usernames)
    retrieved_usernames = {u.username for u in all_users}
    assert retrieved_usernames == set(usernames)

    # Verify all have correct initial values
    for user in all_users:
        assert user.block_count == 0
        assert user.is_blocked is False


# Feature: openai-chat-gateway, Property 4: User data persistence across restarts
@given(
    username=st.text(
        min_size=3,
        max_size=50,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"
        ),
    ),
    block_count=st.integers(min_value=0, max_value=3),
    is_blocked=st.booleans(),
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.unit
async def test_user_data_persistence_across_restarts(
    username: str, block_count: int, is_blocked: bool
) -> None:
    """For any user created, after simulating restart, user should still exist with same data."""
    # Note: For in-memory implementation, we simulate "restart" by creating new instance
    # with same backing store. For real PostgreSQL tests, this would actually reconnect.
    repo = InMemoryRepository()
    await repo.initialize()

    # Create and update user
    user = await repo.create_user(username)
    user.block_count = block_count
    user.is_blocked = is_blocked
    await repo.update_user(user)

    # Simulate restart by keeping the data but "reconnecting"
    # (In real PostgreSQL test, this would close and reopen connection)
    original_data = repo.users.copy()
    await repo.close()

    # "Restart" - new instance with same data
    repo2 = InMemoryRepository()
    repo2.users = original_data
    await repo2.initialize()

    # Verify data persisted
    retrieved = await repo2.get_user(username)
    assert retrieved is not None
    assert retrieved.username == username
    assert retrieved.block_count == block_count
    assert retrieved.is_blocked == is_blocked


# Feature: openai-chat-gateway, Property 5: Duplicate username rejection
@given(
    username=st.text(
        min_size=3,
        max_size=50,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"
        ),
    )
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.unit
async def test_duplicate_username_rejection(username: str) -> None:
    """For any username that already exists, attempting to create another should be rejected."""
    repo = InMemoryRepository()
    await repo.initialize()

    # Create user
    await repo.create_user(username)

    # Attempt to create duplicate
    with pytest.raises(ValueError, match="User already exists"):
        await repo.create_user(username)
