"""FastAPI dependency injection setup."""
from functools import lru_cache

from app.core.config import Settings, get_settings
from app.core.protocols import CacheClient, DatabaseRepository, LockManager, OpenAIClient
from app.repositories.postgres_repository import PostgresRepository
from app.repositories.redis_cache import RedisCache
from app.repositories.redis_lock_manager import RedisLockManager
from app.services.chat_service import ChatService
from app.services.content_moderator import ContentModerator
from app.services.openai_client import OpenAIHttpClient
from app.services.user_service import UserService
from app.services.username_cache import UsernameCache


# Singletons for production dependencies
_db_repository: DatabaseRepository | None = None
_cache_client: CacheClient | None = None
_lock_manager: LockManager | None = None
_openai_client: OpenAIClient | None = None


async def get_db() -> DatabaseRepository:
    """Get database repository dependency."""
    global _db_repository
    if _db_repository is None:
        settings = get_settings()
        _db_repository = PostgresRepository(settings.database_url)
        await _db_repository.initialize()
    return _db_repository


async def get_cache() -> CacheClient:
    """Get cache client dependency."""
    global _cache_client
    if _cache_client is None:
        settings = get_settings()
        _cache_client = RedisCache(settings.redis_url)
        await _cache_client.initialize()
    return _cache_client


async def get_lock_manager() -> LockManager:
    """Get lock manager dependency."""
    global _lock_manager
    if _lock_manager is None:
        settings = get_settings()
        _lock_manager = RedisLockManager(settings.redis_url)
        await _lock_manager.initialize()
    return _lock_manager


def get_openai_client() -> OpenAIClient:
    """Get OpenAI client dependency."""
    global _openai_client
    if _openai_client is None:
        settings = get_settings()
        _openai_client = OpenAIHttpClient(settings.openai_api_key, settings.openai_model)
    return _openai_client


async def get_username_cache(
    cache: CacheClient = None, db: DatabaseRepository = None
) -> UsernameCache:
    """Get username cache dependency."""
    if cache is None:
        cache = await get_cache()
    if db is None:
        db = await get_db()
    return UsernameCache(cache, db)


async def get_user_service(
    db: DatabaseRepository = None, username_cache: UsernameCache = None
) -> UserService:
    """Get user service dependency."""
    if db is None:
        db = await get_db()
    if username_cache is None:
        username_cache = await get_username_cache(db=db)
    return UserService(db, username_cache)


async def get_content_moderator(username_cache: UsernameCache = None) -> ContentModerator:
    """Get content moderator dependency."""
    if username_cache is None:
        username_cache = await get_username_cache()
    return ContentModerator(username_cache)


async def get_chat_service(
    user_service: UserService = None,
    content_moderator: ContentModerator = None,
    openai_client: OpenAIClient = None,
    lock_manager: LockManager = None,
) -> ChatService:
    """Get chat service dependency."""
    if user_service is None:
        user_service = await get_user_service()
    if content_moderator is None:
        content_moderator = await get_content_moderator()
    if openai_client is None:
        openai_client = get_openai_client()
    if lock_manager is None:
        lock_manager = await get_lock_manager()
    return ChatService(user_service, content_moderator, openai_client, lock_manager)
