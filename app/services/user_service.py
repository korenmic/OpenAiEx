"""User service for managing user operations."""
from typing import List, Optional, Set

from app.core.protocols import DatabaseRepository
from app.models.user import User
from app.services.username_cache import UsernameCache


class UserService:
    """Service for user management operations."""

    def __init__(self, db: DatabaseRepository, username_cache: UsernameCache):
        """Initialize user service."""
        self.db = db
        self.username_cache = username_cache

    async def create_user(self, username: str) -> User:
        """Create a new user."""
        user = await self.db.create_user(username)
        # Invalidate cache when new user is created
        await self.username_cache.invalidate()
        return user

    async def get_user(self, username: str) -> Optional[User]:
        """Get user by username."""
        return await self.db.get_user(username)

    async def get_all_users(self) -> List[User]:
        """Get all users."""
        return await self.db.get_all_users()

    async def get_all_usernames_except(self, exclude: str) -> Set[str]:
        """Get all usernames except one (for content moderation)."""
        return await self.username_cache.get_usernames_except(exclude)

    async def increment_block_count(self, username: str) -> User:
        """Increment user's block count atomically and update is_blocked status."""
        user = await self.db.get_user(username)
        if not user:
            raise ValueError(f"User not found: {username}")

        user.block_count += 1
        if user.block_count >= 3:
            user.is_blocked = True

        return await self.db.update_user(user)

    async def is_user_blocked(self, username: str) -> bool:
        """Check if user is blocked."""
        user = await self.db.get_user(username)
        if not user:
            return False
        return user.is_blocked

    async def get_or_create_user(self, username: str) -> User:
        """Get existing user or create new one (for auto-creation)."""
        user = await self.db.get_user(username)
        if user:
            return user
        return await self.create_user(username)
