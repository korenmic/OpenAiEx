from fastapi import FastAPI, HTTPException
from openai import OpenAI

from app.schemas import ChatRequest, ChatResponse

"""
ASGI app server using FastAPI + Uvicorn.

This service is intentionally simple:
- no user auth
- no database
- no conversation history
- each request is a single-turn "forward" to OpenAI Responses API

To run locally (once deps are installed):

    uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload

Assumes OPENAI_API_KEY is set in the environment for the OpenAI SDK.
"""

client = OpenAI()
app = FastAPI()


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """
    Man-in-the-middle endpoint.

    - No user identity.
    - No DB or context window yet.
    - Always a single-turn request: just the new message.
    """
    try:
        # For now we hard-code a reasonably cheap chat model.
        # You can swap this for your model negotiator later.
        model_id = "gpt-4.1-mini"

        response = client.responses.create(
            model=model_id,
            input=[{"role": "user", "content": req.message}],
        )

        # Convenience property exposed by the SDK for text output
        reply_text = response.output_text

        return ChatResponse(model=response.model, reply=reply_text)

    except Exception as exc:  # noqa: BLE001
        # In a real service, you'd log this properly.
        raise HTTPException(status_code=500, detail=str(exc)) from exc
