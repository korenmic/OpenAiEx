import logging
import os

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from utils.logging_config import configure_logging

"""
ASGI mongo server using FastAPI + Uvicorn.

This service is wrapping the mongo database of the users,
meant to be used internally only, not exposed to the actual users.

To run locally (once deps are installed):

    uvicorn mongo.server:app --host 0.0.0.0 --port 8001 --reload

"""

configure_logging()
logger = logging.getLogger("openai_ex.mongo")


class UserStatus(BaseModel):
    """Represents the status of a user as seen by the mongo service.

    This will later be backed by a real MongoDB query.
    For now it is a stub that always responds with 404 / not found.
    """

    username: str
    blocked: bool = False


app = FastAPI()


@app.get("/users/{username}", response_model=UserStatus)
async def get_user_status(username: str) -> UserStatus:
    """Stub endpoint representing a Mongo-backed user lookup.

    In a real deployment this would query MongoDB for the user record.
    For now, it always raises a 404 to simulate "no such user".
    """
    pass
