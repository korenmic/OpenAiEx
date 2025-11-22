import pytest
from fastapi.testclient import TestClient
from mongo.server import app
from mongo.db import init_db, get_db_path
import os

# This test ensures that after migration, user listing and user status behavior remains identical.

def test_user_listing_and_status():
    # Initialize DB
    init_db()
    client = TestClient(app)

    # Initially no users
    r = client.get("/users")
    assert r.status_code == 200
    assert r.json() == []

    # User status lookup should 404
    r = client.get("/users/someuser")
    assert r.status_code == 404
