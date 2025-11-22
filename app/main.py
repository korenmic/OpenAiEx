"""Main FastAPI application."""
import signal
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.api import admin, chat, health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # Startup
    settings = get_settings()
    
    # Validate required config
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Initialize admin key
    admin_key = settings.get_or_generate_admin_key()
    app.state.admin_key = admin_key
    
    logger.info("Application starting...")
    logger.info(f"Auto-create users: {settings.auto_create_users}")
    logger.info(f"Model preference: {settings.model_preference}")
    
    # Select best OpenAI model at startup
    from app.core.dependencies import get_selected_model
    selected_model = await get_selected_model()
    logger.info(f"Selected OpenAI model: {selected_model}")
    
    # Initialize database and cache (lazy initialization in dependencies)
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down gracefully...")
    
    # Close connections
    from app.core.dependencies import _db_repository, _cache_client, _lock_manager
    
    if _db_repository:
        await _db_repository.close()
    if _cache_client:
        await _cache_client.close()
    if _lock_manager:
        await _lock_manager.close()
    
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="OpenAI Chat API Gateway",
    description="Cloud-native API gateway for OpenAI Chat with user management and content moderation",
    version="1.0.0",
    lifespan=lifespan
)

# Register exception handlers
from app.core.exceptions import (
    UserNotFoundError, UserAlreadyExistsError, UserBlockedError, OpenAIServiceError,
    user_not_found_handler, user_already_exists_handler, user_blocked_handler,
    openai_service_handler, generic_exception_handler
)

app.add_exception_handler(UserNotFoundError, user_not_found_handler)
app.add_exception_handler(UserAlreadyExistsError, user_already_exists_handler)
app.add_exception_handler(UserBlockedError, user_blocked_handler)
app.add_exception_handler(OpenAIServiceError, openai_service_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include routers
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(admin.router)


# Handle SIGTERM for graceful shutdown
def handle_sigterm(signum, frame):
    """Handle SIGTERM signal."""
    logger.info("Received SIGTERM, initiating graceful shutdown")
    raise KeyboardInterrupt()


signal.signal(signal.SIGTERM, handle_sigterm)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
