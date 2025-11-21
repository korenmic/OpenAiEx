import logging
import os

import httpx
from fastapi import FastAPI, HTTPException
from mongo.db import init_db, list_usernames, increase_block_counter


from utils.logging_config import configure_logging
from utils.schemas import UserStatus

"""
ASGI mongo server using FastAPI + Uvicorn.

This service is wrapping the mongo database of the users,
meant to be used internally only, not exposed to the actual users.

To run locally (once deps are installed):

    uvicorn mongo.server:app --host 0.0.0.0 --port 8001 --reload

"""

configure_logging()
logger = logging.getLogger("openai_ex.mongo")


app = FastAPI()

@app.on_event('startup')
async def startup_event() -> None:
    init_db()


@app.get("/users/{username}", response_model=UserStatus)
async def get_user_status(username: str) -> UserStatus:
    """Stub endpoint representing a Mongo-backed user lookup.

    In a real deployment this would query MongoDB for the user record.
    For now, it always raises a 404 to simulate "no such user".
    """
    raise HTTPException(status_code=404, detail='User not found')

@app.get('/users', response_model=list[str])
async def list_users() -> list[str]:
    """Return the list of known usernames."""
    return list_usernames()


@app.post('/users/{username}/blocks')
async def increase_user_block_counter(username: str) -> dict[str, int]:
    """Increase the block counter for a user and return the new value."""
    new_value = increase_block_counter(username)
    return {'username': username, 'block_counter': new_value}
