"""User data model."""
from sqlmodel import Field, SQLModel
from pydantic import BaseModel


class User(SQLModel, table=True):
    """User model for database."""

    __tablename__ = "users"

    username: str = Field(primary_key=True, max_length=50)
    block_count: int = Field(default=0, ge=0, le=3)
    is_blocked: bool = Field(default=False)


class CreateUserRequest(BaseModel):
    """Request model for creating a user."""

    username: str


class UserResponse(BaseModel):
    """Response model for user data."""

    username: str
    block_count: int
    is_blocked: bool


class ChatRequest(BaseModel):
    """Request model for chat."""

    username: str
    message: str


class ChatResponse(BaseModel):
    """Response model for chat."""

    response: str
    block_count: int
    violation_detected: bool
