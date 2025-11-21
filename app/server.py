import logging
import time
import uuid
from typing import Optional
from functools import lru_cache

import requests
from fastapi import FastAPI, HTTPException
from openai import OpenAI

from mongo.utils import get_mongo_base_url
from utils.consts import BLOCKED_MESSAGE, BLOCK_COUNTER_THRESHOLD
from utils.logging_config import configure_logging
from utils.model_negotiator import pick_cheapest_supported_model
from utils.schemas import ChatRequest, ChatResponse

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


def _check_user_blocked(username: str) -> bool:
    """Best-effort check with the mongo service.

    Any failure to talk to mongo or a missing user will be treated as
    "not blocked". Only a valid response with a block_counter greater
    than or equal to BLOCK_COUNTER_THRESHOLD will block the user.
    """
    mongo_base_url = get_mongo_base_url()
    if mongo_base_url is None:
        logger.warning('mongo_lookup_skipped username=%s reason=missing_env', username)
        return False

    url = f'{mongo_base_url}/users/{username}'
    try:
        mongo_resp = requests.get(url, timeout=1.0)
    except Exception as exc:  # noqa: BLE001
        logger.error('mongo_lookup_failed username=%s error=%r', username, exc)
        return False

    if mongo_resp.status_code == 404:
        logger.error('mongo_user_not_found username=%s', username)
        return False

    if mongo_resp.status_code >= 400:
        logger.error(
            'mongo_user_error username=%s status=%s',
            username,
            mongo_resp.status_code,
        )
        return False

    try:
        data = mongo_resp.json()
    except ValueError:
        logger.error('mongo_user_bad_json username=%s', username)
        return False

    block_counter = data.get('block_counter', 0)
    try:
        counter_value = int(block_counter)
    except (TypeError, ValueError) as e:
        logger.error('mongo_user_bad_block_counter_value username=%s', username)
        counter_value = 0

    is_blocked = counter_value >= BLOCK_COUNTER_THRESHOLD
    logger.info(
        'mongo_user_status username=%s block_counter=%s blocked=%s',
        username,
        counter_value,
        is_blocked,
    )
    return is_blocked


def _get_usernames():
    # TODO - keep usernames cached in ram, if mongo or us (this app) contacts us for username update
    #        then update the cache, preventing us from accessing mongo lots of times
    #        maybe add timed out lru style cache
    mongo_base_url = get_mongo_base_url()
    all_usernames = []
    if mongo_base_url is not None:
        try:
            url = f'{mongo_base_url}/users'
            resp = requests.get(url, timeout=1.0)
            all_usernames = resp.json()
        except Exception:  # noqa: BLE001
            all_usernames = []
    return all_usernames


def _users_except(username: str) -> list[str]:
    all_usernames = _get_usernames()
    return [name for name in all_usernames if name != username]
    

def _check_for_illegal_words(message: str, username: str) -> bool:
    """
    Look for other usernames (except the name of the current user),
    simple split by whitespace
    """
    return any(set(message.split()) & set(_users_except(username)))


def _increase_block_counter(username: str) -> None:
    # TODO - TBD
    pass


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

    if _check_user_blocked(req.username):
        logger.warning(f'Blocked user {req.username} attempting to chat')
        return ChatResponse(model='', reply=BLOCKED_MESSAGE)
    illegal_words_found = _check_for_illegal_words(req.message, req.username)
    if illegal_words_found:
        _increase_block_counter(req.username)

    try:
        model_id = get_model_id()

        # TODO - get history, append it to the req.message before sending the input
        #        then we can delete hello_world is it holds no more unimplemented POC parts
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
