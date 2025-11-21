"""Custom exceptions and exception handlers."""
from fastapi import Request, status
from fastapi.responses import JSONResponse


class UserNotFoundError(Exception):
    """User not found exception."""
    pass


class UserAlreadyExistsError(Exception):
    """User already exists exception."""
    pass


class UserBlockedError(Exception):
    """User is blocked exception."""
    pass


class OpenAIServiceError(Exception):
    """OpenAI service error exception."""
    pass


async def user_not_found_handler(request: Request, exc: UserNotFoundError) -> JSONResponse:
    """Handle user not found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)}
    )


async def user_already_exists_handler(request: Request, exc: UserAlreadyExistsError) -> JSONResponse:
    """Handle user already exists errors."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)}
    )


async def user_blocked_handler(request: Request, exc: UserBlockedError) -> JSONResponse:
    """Handle user blocked errors."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc)}
    )


async def openai_service_handler(request: Request, exc: OpenAIServiceError) -> JSONResponse:
    """Handle OpenAI service errors."""
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": f"Upstream service error: {str(exc)}"}
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle generic exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )
