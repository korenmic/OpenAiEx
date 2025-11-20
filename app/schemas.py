from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request schema for the /chat endpoint."""

    username: str
    message: str


class ChatResponse(BaseModel):
    """Response schema for the /chat endpoint."""

    model: str
    reply: str
