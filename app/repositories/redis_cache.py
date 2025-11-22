"""Redis cache implementation."""
from typing import Optional

import redis.asyncio as aioredis


class RedisCache:
    """Redis implementation of CacheClient protocol."""

    def __init__(self, redis_url: str):
        """Initialize Redis cache."""
        self.redis_url = redis_url
        self.client: Optional[aioredis.Redis] = None

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        self.client = await aioredis.from_url(self.redis_url, decode_responses=True)

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        if not self.client:
            raise RuntimeError("Redis not initialized")
        return await self.client.get(key)

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        if not self.client:
            raise RuntimeError("Redis not initialized")

        if ttl:
            await self.client.setex(key, ttl, value)
        else:
            await self.client.set(key, value)

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        if not self.client:
            raise RuntimeError("Redis not initialized")
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.client:
            raise RuntimeError("Redis not initialized")
        result = await self.client.exists(key)
        return bool(result)

    async def health_check(self) -> bool:
        """Check Redis connectivity."""
        if not self.client:
            return False

        try:
            await self.client.ping()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close Redis connections."""
        if self.client:
            await self.client.close()
