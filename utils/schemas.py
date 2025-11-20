from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request schema for the /chat endpoint."""

    username: str
    message: str


class ChatResponse(BaseModel):
    """Response schema for the /chat endpoint."""

    model: str
    reply: str


class UserStatus(BaseModel):
    """Represents the status of a user as seen by the mongo service.

    This will later be backed by a real MongoDB query.
    For now it is a stub that always responds with 404 / not found.
    """

    username: str
    blocked: bool = False
