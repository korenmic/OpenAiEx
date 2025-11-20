import logging
import time
import uuid
from fastapi import FastAPI, HTTPException
from openai import OpenAI
from utils.logging_config import configure_logging
from utils.model_negotiator import pick_cheapest_supported_model

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

configure_logging()
logger = logging.getLogger('openai_ex.app')

client = OpenAI()

# Decide on the cheapest supported chat model once at startup,
# using the same negotiator logic as in hello_world.py.
NEGOTIATED_MODEL_ID, NEGOTIATED_MODEL_PRICE = pick_cheapest_supported_model(client)
app = FastAPI()


@app.post('/chat', response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """
    Man-in-the-middle endpoint.

    - No user identity.
    - No DB or context window yet.
    - Always a single-turn request: just the new message.
    """
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    logger.info("chat_request id=%s message=%r", request_id, req.message)

    try:
        model_id = NEGOTIATED_MODEL_ID

        response = client.responses.create(
            model=model_id,
            input=[{'role': 'user', 'content': req.message}],
        )

        latency = time.perf_counter() - start
        logger.info(
            'chat_response id=%s model=%s latency=%.3fs',
            request_id,
            response.model,
            latency,
        )

        reply_text = response.output_text

        return ChatResponse(model=response.model, reply=reply_text)

    except Exception as exc:  # noqa: BLE001
        logger.exception('chat_error id=%s', request_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
