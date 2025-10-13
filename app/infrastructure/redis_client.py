"""
Redis Client Integration

Provides connection pooling and helper methods for Redis operations.
Follows the Singleton pattern to ensure a single Redis connection pool.
"""

import logging
from typing import Any

from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Redis Client Class
# ============================================================================


class RedisClient:
    """
    Redis client with connection pooling.

    This class implements the Singleton pattern to ensure only one
    connection pool is created throughout the application lifecycle.
    """

    _instance: "RedisClient | None" = None
    _pool: ConnectionPool | None = None
    _client: Redis | None = None

    def __new__(cls) -> "RedisClient":
        """Ensure only one instance exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self) -> None:
        """
        Initialize Redis connection pool.

        This method should be called during application startup.
        """
        if self._pool is not None:
            logger.warning("Redis connection pool already exists")
            return

        try:
            # Build Redis URL
            if settings.redis_password:
                redis_url = f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
            else:
                redis_url = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"

            # Create connection pool
            self._pool = ConnectionPool.from_url(
                redis_url,
                max_connections=settings.redis_max_connections,
                decode_responses=True,
            )

            # Create client
            self._client = Redis(connection_pool=self._pool)

            # Test connection
            await self._client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error("Failed to connect to Redis: %s", e)
            raise

    async def disconnect(self) -> None:
        """
        Close Redis connection pool.

        This method should be called during application shutdown.
        """
        if self._client:
            await self._client.aclose()  # type: ignore[attr-defined]
            self._client = None

        if self._pool:
            await self._pool.aclose()  # type: ignore[attr-defined]
            self._pool = None

        logger.info("Redis connection closed")

    def get_client(self) -> Redis:
        """
        Get Redis client instance.

        Returns:
            Redis client instance

        Raises:
            RuntimeError: If client is not initialized
        """
        if self._client is None:
            raise RuntimeError("Redis client not initialized. Call connect() first.")
        return self._client

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def get(self, key: str) -> str | None:
        """Get value by key."""
        client = self.get_client()
        return await client.get(key)

    async def set(
        self,
        key: str,
        value: str,
        ex: int | None = None,
        px: int | None = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool | None:
        """
        Set key-value pair.

        Args:
            key: Key name
            value: Value to store
            ex: Expiration time in seconds
            px: Expiration time in milliseconds
            nx: Only set if key doesn't exist
            xx: Only set if key exists

        Returns:
            True if successful
        """
        client = self.get_client()
        return await client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)

    async def delete(self, *keys: str) -> int:
        """
        Delete one or more keys.

        Returns:
            Number of keys deleted
        """
        client = self.get_client()
        return await client.delete(*keys)

    async def exists(self, *keys: str) -> int:
        """
        Check if keys exist.

        Returns:
            Number of existing keys
        """
        client = self.get_client()
        return await client.exists(*keys)

    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key.

        Args:
            key: Key name
            seconds: Expiration time in seconds

        Returns:
            True if successful
        """
        client = self.get_client()
        return await client.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """
        Get remaining TTL for a key.

        Returns:
            TTL in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        client = self.get_client()
        return await client.ttl(key)

    async def incr(self, key: str, amount: int = 1) -> int:
        """
        Increment value by amount.

        Returns:
            New value after increment
        """
        client = self.get_client()
        return await client.incrby(key, amount)

    async def decr(self, key: str, amount: int = 1) -> int:
        """
        Decrement value by amount.

        Returns:
            New value after decrement
        """
        client = self.get_client()
        return await client.decrby(key, amount)

    async def hset(self, name: str, mapping: dict[str, Any]) -> int:
        """
        Set hash field values.

        Returns:
            Number of fields added
        """
        client = self.get_client()
        return await client.hset(name, mapping=mapping)  # type: ignore[arg-type]

    async def hget(self, name: str, key: str) -> str | None:
        """Get hash field value."""
        client = self.get_client()
        return await client.hget(name, key)

    async def hgetall(self, name: str) -> dict[str, str]:
        """Get all hash fields and values."""
        client = self.get_client()
        return await client.hgetall(name)

    async def hdel(self, name: str, *keys: str) -> int:
        """
        Delete hash fields.

        Returns:
            Number of fields deleted
        """
        client = self.get_client()
        return await client.hdel(name, *keys)


# ============================================================================
# Global Instance
# ============================================================================

redis_client = RedisClient()


# ============================================================================
# Dependency for FastAPI
# ============================================================================


async def get_redis() -> Redis:
    """
    FastAPI dependency to get Redis client.

    Usage:
        @router.get("/items")
        async def get_items(redis: Redis = Depends(get_redis)):
            await redis.set("key", "value")
            return {"status": "ok"}
    """
    return redis_client.get_client()
