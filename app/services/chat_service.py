"""Chat service for orchestrating chat requests."""
from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.core.protocols import LockManager, OpenAIClient
from app.models.user import ChatResponse
from app.services.content_moderator import ContentModerator
from app.services.openai_client import OpenAIServiceError
from app.services.user_service import UserService


class ChatService:
    """Service for orchestrating chat requests with moderation and blocking."""

    def __init__(
        self,
        user_service: UserService,
        content_moderator: ContentModerator,
        openai_client: OpenAIClient,
        lock_manager: LockManager,
    ):
        """Initialize chat service."""
        self.user_service = user_service
        self.content_moderator = content_moderator
        self.openai_client = openai_client
        self.lock_manager = lock_manager
        self.settings = get_settings()

    async def process_chat_request(self, username: str, message: str) -> ChatResponse:
        """
        Process chat request with full orchestration:
        1. Acquire per-user distributed lock
        2. Get or create user (if auto-creation enabled)
        3. Check if blocked
        4. Content moderation check
        5. Increment block count if violations found
        6. Forward to OpenAI
        7. Return response
        8. Release lock (via context manager)
        """
        # Acquire per-user lock to serialize requests from same user
        async with self.lock_manager.acquire_lock(f"user:{username}"):
            # Get or create user
            if self.settings.auto_create_users:
                user = await self.user_service.get_or_create_user(username)
            else:
                user = await self.user_service.get_user(username)
                if not user:
                    raise ValueError(f"User not found: {username}")

            # Check if blocked and auto-unblock if duration expired
            if user.is_blocked:
                if user.blocked_at:
                    # Check if block duration has expired
                    block_expiry = user.blocked_at + timedelta(hours=self.settings.block_duration_hours)
                    now = datetime.now(timezone.utc)
                    
                    if now >= block_expiry:
                        # Automatically unblock user
                        user = await self.user_service.unblock_user(username)
                        # Continue processing request
                    else:
                        raise PermissionError(f"User is blocked and cannot make requests")
                else:
                    # Blocked but no timestamp (legacy data), still block
                    raise PermissionError(f"User is blocked and cannot make requests")

            # Content moderation check
            violations = await self.content_moderator.check_for_violations(message, username)
            violation_detected = len(violations) > 0

            # Increment block count if violations found
            if violation_detected:
                user = await self.user_service.increment_block_count(username)

            # Forward to OpenAI (even if violation detected)
            try:
                response_text = await self.openai_client.send_chat_request(message)
            except OpenAIServiceError as e:
                # Propagate OpenAI errors
                raise

            # Return response with metadata
            return ChatResponse(
                response=response_text,
                block_count=user.block_count,
                violation_detected=violation_detected,
            )
