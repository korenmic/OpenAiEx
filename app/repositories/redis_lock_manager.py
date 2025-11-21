"""Redis distributed lock manager implementation."""
import asyncio
import secrets
from contextlib import asynccontextmanager
from typing import Optional

import redis.asyncio as aioredis


class RedisLockManager:
    """Distributed locks using Redis."""

    def __init__(self, redis_url: str):
        """Initialize Redis lock manager."""
        self.redis_url = redis_url
        self.client: Optional[aioredis.Redis] = None

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        self.client = await aioredis.from_url(self.redis_url, decode_responses=True)

    @asynccontextmanager
    async def acquire_lock(self, key: str, timeout: float = 30.0):
        """Acquire distributed lock with timeout."""
        if not self.client:
            raise RuntimeError("Redis not initialized")

        lock_key = f"lock:{key}"
        lock_value = secrets.token_hex(16)

        # Try to acquire lock
        acquired = await self.client.set(
            lock_key, lock_value, ex=int(timeout), nx=True  # Only set if not exists
        )

        if not acquired:
            # Wait for lock to be released
            for _ in range(int(timeout * 10)):
                await asyncio.sleep(0.1)
                acquired = await self.client.set(lock_key, lock_value, ex=int(timeout), nx=True)
                if acquired:
                    break
            else:
                raise TimeoutError(f"Could not acquire lock for {key}")

        try:
            yield
        finally:
            # Release lock only if we still own it
            script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            await self.client.eval(script, 1, lock_key, lock_value)

    async def close(self) -> None:
        """Close Redis connections."""
        if self.client:
            await self.client.close()
