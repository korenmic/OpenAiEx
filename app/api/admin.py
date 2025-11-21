"""Admin endpoints for user management."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import verify_admin_key
from app.core.dependencies import get_user_service
from app.models.user import CreateUserRequest, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    user_service: UserService = Depends(get_user_service),
    admin_key: str = Depends(verify_admin_key),
) -> UserResponse:
    """Create a new user (admin only)."""
    try:
        user = await user_service.create_user(request.username)
        return UserResponse(
            username=user.username, block_count=user.block_count, is_blocked=user.is_blocked
        )
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/users/{username}", response_model=UserResponse)
async def get_user(
    username: str,
    user_service: UserService = Depends(get_user_service),
    admin_key: str = Depends(verify_admin_key),
) -> UserResponse:
    """Get user by username (admin only)."""
    user = await user_service.get_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User not found: {username}"
        )

    return UserResponse(
        username=user.username, block_count=user.block_count, is_blocked=user.is_blocked
    )


@router.get("/users", response_model=dict)
async def list_users(
    user_service: UserService = Depends(get_user_service),
    admin_key: str = Depends(verify_admin_key),
) -> dict:
    """List all users (admin only)."""
    users = await user_service.get_all_users()
    return {
        "users": [
            UserResponse(
                username=u.username, block_count=u.block_count, is_blocked=u.is_blocked
            )
            for u in users
        ]
    }
