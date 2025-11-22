"""Property-based tests for concurrency behavior."""
import asyncio

import pytest
from hypothesis import given, settings, strategies as st

from app.tests.mocks import InMemoryRepository, LocalLockManager, MockOpenAIClient


# Feature: openai-chat-gateway, Property 8: Concurrent chat requests complete successfully (different users)
@given(
    usernames=st.lists(
        st.text(
            min_size=3,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"
            ),
        ),
        min_size=2,
        max_size=5,
        unique=True,
    )
)
@settings(max_examples=50)
@pytest.mark.asyncio
@pytest.mark.unit
async def test_concurrent_requests_from_different_users(usernames: list[str]) -> None:
    """For any set of non-blocked users, concurrent chat requests should complete successfully."""
    repo = InMemoryRepository()
    lock_manager = LocalLockManager()
    openai_client = MockOpenAIClient()

    await repo.initialize()

    # Create all users
    for username in usernames:
        await repo.create_user(username)

    # Simulate concurrent chat requests from different users
    async def make_request(username: str) -> str:
        async with lock_manager.acquire_lock(f"user:{username}"):
            # Simulate some processing
            await asyncio.sleep(0.01)
            response = await openai_client.send_chat_request(f"Hello from {username}")
            return response

    # Send concurrent requests
    tasks = [make_request(username) for username in usernames]
    responses = await asyncio.gather(*tasks)

    # All requests should complete successfully
    assert len(responses) == len(usernames)
    assert all(isinstance(r, str) for r in responses)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_same_user_requests_are_serialized() -> None:
    """Requests from the same user should be serialized (not concurrent)."""
    repo = InMemoryRepository()
    lock_manager = LocalLockManager()
    openai_client = MockOpenAIClient()

    await repo.initialize()
    await repo.create_user("alice")

    execution_order = []

    async def make_request(request_id: int) -> str:
        async with lock_manager.acquire_lock("user:alice"):
            execution_order.append(f"start_{request_id}")
            await asyncio.sleep(0.05)  # Simulate processing
            execution_order.append(f"end_{request_id}")
            response = await openai_client.send_chat_request(f"Request {request_id}")
            return response

    # Send 2 concurrent requests from same user
    task1 = asyncio.create_task(make_request(1))
    task2 = asyncio.create_task(make_request(2))

    responses = await asyncio.gather(task1, task2)

    # Both should complete
    assert len(responses) == 2

    # Verify serialization: one request should fully complete before the other starts
    # Valid patterns: [start_1, end_1, start_2, end_2] or [start_2, end_2, start_1, end_1]
    assert len(execution_order) == 4

    # Check that starts and ends are properly nested (no interleaving)
    if execution_order[0] == "start_1":
        assert execution_order == ["start_1", "end_1", "start_2", "end_2"]
    else:
        assert execution_order == ["start_2", "end_2", "start_1", "end_1"]
