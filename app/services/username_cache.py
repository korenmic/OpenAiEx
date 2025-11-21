"""Username caching service."""
from typing import Set

from app.core.protocols import CacheClient, DatabaseRepository


class UsernameCache:
    """Redis-backed username cache with simple invalidation."""

    CACHE_KEY = "usernames:all"

    def __init__(self, redis: CacheClient, db: DatabaseRepository):
        """Initialize username cache."""
        self.redis = redis
        self.db = db

    async def get_usernames_except(self, exclude: str) -> Set[str]:
        """Get all usernames except one, using cache."""
        # Try cache first
        cached = await self.redis.get(self.CACHE_KEY)
        if cached:
            usernames = set(cached.split(",")) if cached else set()
        else:
            # Cache miss - query database and populate cache
            usernames = set(await self.db.get_all_usernames())
            if usernames:
                await self.redis.set(self.CACHE_KEY, ",".join(usernames))

        # Remove excluded username
        usernames.discard(exclude)
        return usernames

    async def invalidate(self) -> None:
        """Invalidate cache when users are created - simple deletion."""
        await self.redis.delete(self.CACHE_KEY)
