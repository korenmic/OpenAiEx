"""Protocol definitions for abstraction layer."""
from typing import AsyncContextManager, List, Optional, Protocol

from app.models.user import User


class DatabaseRepository(Protocol):
    """Protocol for database operations."""

    async def create_user(self, username: str) -> User:
        """Create a new user."""
        ...

    async def get_user(self, username: str) -> Optional[User]:
        """Get user by username."""
        ...

    async def get_all_users(self) -> List[User]:
        """Get all users."""
        ...

    async def get_all_usernames(self) -> List[str]:
        """Get all usernames (optimized query)."""
        ...

    async def update_user(self, user: User) -> User:
        """Update user."""
        ...

    async def initialize(self) -> None:
        """Initialize database (create tables)."""
        ...

    async def health_check(self) -> bool:
        """Check database connectivity."""
        ...

    async def close(self) -> None:
        """Close database connections."""
        ...


class CacheClient(Protocol):
    """Protocol for cache operations."""

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        ...

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        ...

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        ...

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        ...

    async def health_check(self) -> bool:
        """Check cache connectivity."""
        ...

    async def close(self) -> None:
        """Close cache connections."""
        ...


class LockManager(Protocol):
    """Protocol for distributed locking."""

    def acquire_lock(self, key: str, timeout: float = 30.0) -> AsyncContextManager[None]:
        """Acquire distributed lock with timeout."""
        ...


class OpenAIClient(Protocol):
    """Protocol for OpenAI API operations."""

    async def send_chat_request(self, message: str) -> str:
        """Send chat request to OpenAI and return response."""
        ...
