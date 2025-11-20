import os

from fastapi.testclient import TestClient

from app.server import app
from app.schemas import ChatRequest, ChatResponse


client = TestClient(app)


def test_chat_endpoint_roundtrip() -> None:
    """Basic sanity test for the /chat endpoint.

    This test assumes that OPENAI_API_KEY is set in the environment.
    It exercises the FastAPI app in-process (no external server needed).
    """
    if 'OPENAI_API_KEY' not in os.environ:
        # Make it explicit why the test would otherwise fail.
        raise RuntimeError('OPENAI_API_KEY must be set for this test to run.')

    payload = ChatRequest(message="Hello from pytest")
    resp = client.post("/chat", json=payload.model_dump())

    assert resp.status_code == 200

    data = ChatResponse(**resp.json())
    assert isinstance(data.reply, str)
    assert data.reply.strip()
