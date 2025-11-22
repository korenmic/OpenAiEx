"""Mock implementations for testing."""
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

from app.models.user import User


class InMemoryRepository:
    """In-memory implementation of DatabaseRepository for testing."""

    def __init__(self) -> None:
        """Initialize in-memory repository."""
        self.users: Dict[str, User] = {}

    async def create_user(self, username: str) -> User:
        """Create a new user."""
        if username in self.users:
            raise ValueError(f"User already exists: {username}")

        user = User(username=username, block_count=0, is_blocked=False)
        self.users[username] = user
        return user

    async def get_user(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.users.get(username)

    async def get_all_users(self) -> List[User]:
        """Get all users."""
        return list(self.users.values())

    async def get_all_usernames(self) -> List[str]:
        """Get all usernames."""
        return list(self.users.keys())

    async def update_user(self, user: User) -> User:
        """Update user."""
        self.users[user.username] = user
        return user

    async def initialize(self) -> None:
        """Initialize (no-op for in-memory)."""
        pass

    async def health_check(self) -> bool:
        """Check health (always healthy for in-memory)."""
        return True

    async def close(self) -> None:
        """Close (no-op for in-memory)."""
        pass


class InMemoryCache:
    """In-memory implementation of CacheClient for testing."""

    def __init__(self) -> None:
        """Initialize in-memory cache."""
        self.data: Dict[str, str] = {}

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        return self.data.get(key)

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        self.data[key] = value

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        self.data.pop(key, None)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return key in self.data

    async def health_check(self) -> bool:
        """Check health (always healthy for in-memory)."""
        return True

    async def close(self) -> None:
        """Close (no-op for in-memory)."""
        pass


class LocalLockManager:
    """Local lock manager using asyncio.Lock for testing."""

    def __init__(self) -> None:
        """Initialize local lock manager."""
        self.locks: Dict[str, asyncio.Lock] = {}

    @asynccontextmanager
    async def acquire_lock(self, key: str, timeout: float = 30.0):
        """Acquire lock."""
        if key not in self.locks:
            self.locks[key] = asyncio.Lock()

        lock = self.locks[key]
        async with lock:
            yield


class MockOpenAIClient:
    """Mock OpenAI client for testing."""

    def __init__(self, responses: Optional[List[str]] = None):
        """Initialize mock client with predefined responses."""
        self.responses = responses or ["This is a mock response from OpenAI."]
        self.call_count = 0
        self.last_message: Optional[str] = None

    async def send_chat_request(self, message: str) -> str:
        """Send chat request (returns mock response)."""
        self.last_message = message
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return response
