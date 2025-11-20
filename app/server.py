import logging
import os
import time
import uuid
import requests
from typing import Optional
from functools import lru_cache
from fastapi import FastAPI, HTTPException
from openai import OpenAI
from utils.logging_config import configure_logging
from utils.model_negotiator import pick_cheapest_supported_model
from utils.schemas import ChatRequest, ChatResponse

from app.consts import BLOCKED_MESSAGE
from mongo.utils import get_mongo_base_url

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


@lru_cache()
def get_client():
    return OpenAI()


@lru_cache()
def get_model_id():
    """
    Decide on the cheapest supported chat model once at startup,
    """
    model_id, _ = pick_cheapest_supported_model(get_client())
    return model_id


app = FastAPI()


def _get_user_status(request_id, req) -> Optional[bool]:
    """
    Best-effort check with the mongo service.
    is logged but does not block the request if user is missing.
    """
    mongo_base_url = get_mongo_base_url()
    if mongo_base_url is None:
        logger.warning('mongo_lookup_skipped id=%s username=%s reason=missing_env', request_id, req.username)
        return

    url = f'{mongo_base_url}/users/{req.username}'
    try:
        mongo_resp = requests.get(url, timeout=1.0)
        if mongo_resp.status_code == 404:
            logger.error('mongo_user_not_found id=%s username=%s', request_id, req.username)
        elif mongo_resp.status_code >= 400:
            logger.error(
                'mongo_user_error id=%s username=%s status=%s',
                request_id,
                req.username,
                mongo_resp.status_code,
            )
        else:
            # In the future we can inspect mongo_resp.json() for a `blocked` flag.
            logger.info('mongo_user_ok id=%s username=%s', request_id, req.username)
    except Exception as exc:
        logger.error('mongo_lookup_failed id=%s username=%s error=%r', request_id, req.username, exc)
    # TODO - actually extract from mongo_resp the blocked status and return it as a bool


@app.post('/chat', response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """
    Man-in-the-middle endpoint.

    - No user identity beyond the provided username.
    - No DB or context window yet.
    - Always a single-turn request: just the new message.
    """
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    logger.info('chat_request id=%s username=%s message=%r', request_id, req.username, req.message)

    if user_status := _get_user_status(request_id, req) is False:
        return ChatResponse(model='', reply=BLOCKED_MESSAGE)

    try:
        model_id = get_model_id()

        response = get_client().responses.create(
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
