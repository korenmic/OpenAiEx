"""Property-based tests for content moderator."""
import pytest
from hypothesis import given, settings, strategies as st

from app.services.content_moderator import ContentModerator
from app.services.username_cache import UsernameCache
from app.tests.mocks import InMemoryCache, InMemoryRepository


# Feature: openai-chat-gateway, Property 10: Username mention detection
@given(
    mentioned_username=st.text(
        min_size=3,
        max_size=20,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"
        ),
    ),
    requesting_username=st.text(
        min_size=3,
        max_size=20,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"
        ),
    ),
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.unit
async def test_username_mention_detection(
    mentioned_username: str, requesting_username: str
) -> None:
    """For any message containing an existing username as a complete word, it should be detected."""
    # Ensure usernames are different
    if mentioned_username.lower() == requesting_username.lower():
        return

    repo = InMemoryRepository()
    cache = InMemoryCache()
    username_cache = UsernameCache(cache, repo)
    moderator = ContentModerator(username_cache)

    await repo.initialize()

    # Create users
    await repo.create_user(requesting_username)
    await repo.create_user(mentioned_username)

    # Create message with mentioned username as complete word
    message = f"Hello {mentioned_username} how are you?"

    # Check for violations
    violations = await moderator.check_for_violations(message, requesting_username)

    # Should detect the mention
    assert len(violations) > 0
    assert mentioned_username in violations or mentioned_username.lower() in [
        v.lower() for v in violations
    ]


# Feature: openai-chat-gateway, Property 13: Case-insensitive username matching
@given(
    username=st.text(
        min_size=3,
        max_size=20,
        alphabet=st.characters(whitelist_categories=("Lu", "Ll"), whitelist_characters="_"),
    ),
    requesting_username=st.text(
        min_size=3,
        max_size=20,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"
        ),
    ),
    case_variant=st.sampled_from(["upper", "lower", "title"]),
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.unit
async def test_case_insensitive_username_matching(
    username: str, requesting_username: str, case_variant: str
) -> None:
    """For any username, all case variations should be detected as violations."""
    # Ensure usernames are different
    if username.lower() == requesting_username.lower():
        return

    repo = InMemoryRepository()
    cache = InMemoryCache()
    username_cache = UsernameCache(cache, repo)
    moderator = ContentModerator(username_cache)

    await repo.initialize()

    # Create users
    await repo.create_user(requesting_username)
    await repo.create_user(username)

    # Create message with case variant
    if case_variant == "upper":
        variant = username.upper()
    elif case_variant == "lower":
        variant = username.lower()
    else:  # title
        variant = username.title()

    message = f"Hello {variant} how are you?"

    # Check for violations
    violations = await moderator.check_for_violations(message, requesting_username)

    # Should detect the mention regardless of case
    assert len(violations) > 0


# Feature: openai-chat-gateway, Property 14: Exact match only (no substring matching)
@given(
    username=st.text(
        min_size=3,
        max_size=10,
        alphabet=st.characters(whitelist_categories=("Ll",), whitelist_characters=""),
    ),
    requesting_username=st.text(
        min_size=3,
        max_size=20,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"
        ),
    ),
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.unit
async def test_exact_match_only_no_substring(username: str, requesting_username: str) -> None:
    """For any username, if it appears as substring within another word, it should NOT be detected."""
    # Ensure usernames are different
    if username.lower() == requesting_username.lower():
        return

    repo = InMemoryRepository()
    cache = InMemoryCache()
    username_cache = UsernameCache(cache, repo)
    moderator = ContentModerator(username_cache)

    await repo.initialize()

    # Create users
    await repo.create_user(requesting_username)
    await repo.create_user(username)

    # Create message where username is part of another word (substring)
    # For example, if username is "alice", use "palace" or "malice"
    message = f"I went to the p{username}s yesterday"

    # Check for violations
    violations = await moderator.check_for_violations(message, requesting_username)

    # Should NOT detect the mention (it's a substring, not a complete word)
    assert username not in violations

    # Now test with username as complete word
    message_with_word = f"Hello {username} how are you?"
    violations_with_word = await moderator.check_for_violations(
        message_with_word, requesting_username
    )

    # Should detect when it's a complete word
    assert len(violations_with_word) > 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_no_violations_when_no_mentions() -> None:
    """Messages without username mentions should return empty violations list."""
    repo = InMemoryRepository()
    cache = InMemoryCache()
    username_cache = UsernameCache(cache, repo)
    moderator = ContentModerator(username_cache)

    await repo.initialize()

    await repo.create_user("alice")
    await repo.create_user("bob")

    message = "Hello world, this is a test message"

    violations = await moderator.check_for_violations(message, "alice")

    assert len(violations) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_user_cannot_mention_themselves() -> None:
    """User mentioning their own username should not be a violation."""
    repo = InMemoryRepository()
    cache = InMemoryCache()
    username_cache = UsernameCache(cache, repo)
    moderator = ContentModerator(username_cache)

    await repo.initialize()

    await repo.create_user("alice")

    message = "I am alice and this is my message"

    violations = await moderator.check_for_violations(message, "alice")

    assert len(violations) == 0
