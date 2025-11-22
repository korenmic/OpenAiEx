"""Integration test configuration and fixtures."""
import os
import pytest
import subprocess
from typing import AsyncGenerator

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlmodel import SQLModel

from app.core.config import get_settings
from app.core.dependencies import get_db, get_cache, get_lock_manager, get_openai_client
from app.repositories.postgres_repository import PostgresRepository
from app.repositories.redis_cache import RedisCache
from app.repositories.redis_lock_manager import RedisLockManager
from app.tests.mocks import MockOpenAIClient

# Set test environment variables
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("ADMIN_API_KEY", "test-admin-key")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://localhost:5432/gateway_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")  # Use DB 1 for tests


@pytest.fixture(scope="session")
def ensure_postgres():
    """Ensure PostgreSQL is running."""
    # Try to start PostgreSQL if not running (WSL/Linux)
    try:
        subprocess.run(["sudo", "service", "postgresql", "status"], 
                      capture_output=True, check=False)
        result = subprocess.run(["sudo", "service", "postgresql", "start"], 
                               capture_output=True, check=False)
        if result.returncode != 0:
            pytest.skip("PostgreSQL not available")
    except FileNotFoundError:
        # Not on Linux/WSL, assume PostgreSQL is managed externally
        pass
    
    yield
    
    # Cleanup is handled by test database teardown


@pytest.fixture(scope="session")
def ensure_redis():
    """Ensure Redis is running."""
    # Try to start Redis if not running (WSL/Linux)
    try:
        subprocess.run(["sudo", "service", "redis-server", "status"], 
                      capture_output=True, check=False)
        result = subprocess.run(["sudo", "service", "redis-server", "start"], 
                               capture_output=True, check=False)
        if result.returncode != 0:
            pytest.skip("Redis not available")
    except FileNotFoundError:
        # Not on Linux/WSL, assume Redis is managed externally
        pass
    
    yield


@pytest.fixture(scope="function")
async def test_db(ensure_postgres) -> AsyncGenerator[PostgresRepository, None]:
    """Create a test database repository with clean state."""
    settings = get_settings()
    db = PostgresRepository(settings.database_url)
    
    # Initialize database and create tables
    await db.initialize()
    
    yield db
    
    # Cleanup: Drop all data
    if db.engine:
        async with db.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
        await db.close()


@pytest.fixture(scope="function")
async def test_cache(ensure_redis) -> AsyncGenerator[RedisCache, None]:
    """Create a test Redis cache with clean state."""
    settings = get_settings()
    cache = RedisCache(settings.redis_url)
    
    await cache.initialize()
    
    yield cache
    
    # Cleanup: Flush test database
    if cache.redis:
        await cache.redis.flushdb()
        await cache.close()


@pytest.fixture(scope="function")
async def test_lock_manager(ensure_redis) -> AsyncGenerator[RedisLockManager, None]:
    """Create a test lock manager."""
    settings = get_settings()
    lock_manager = RedisLockManager(settings.redis_url)
    
    await lock_manager.initialize()
    
    yield lock_manager
    
    # Cleanup
    if lock_manager.redis:
        await lock_manager.close()


@pytest.fixture
def mock_openai() -> MockOpenAIClient:
    """Create a mock OpenAI client."""
    return MockOpenAIClient()


@pytest.fixture
def integration_app(test_db, test_cache, test_lock_manager, mock_openai) -> FastAPI:
    """Create FastAPI app with real DB/Redis but mocked OpenAI."""
    from app.main import app
    
    # Override dependencies with test instances
    app.dependency_overrides[get_db] = lambda: test_db
    app.dependency_overrides[get_cache] = lambda: test_cache
    app.dependency_overrides[get_lock_manager] = lambda: test_lock_manager
    app.dependency_overrides[get_openai_client] = lambda: mock_openai
    
    yield app
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Reset settings cache between tests."""
    import app.core.config as config_module
    
    config_module._settings = None
    yield
    config_module._settings = None
