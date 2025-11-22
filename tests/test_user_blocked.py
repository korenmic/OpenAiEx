import os
import time
import requests

import pytest


from utils.consts import BLOCKED_MESSAGE

APP_BASE = os.environ.get('APP_BASE_URL', 'http://localhost:8000')
MONGO_BASE = os.environ.get('MONGO_BASE_URL', 'http://localhost:8001')


def _wait_for(url: str, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=1.0)
            if r.status_code < 500:
                return
        except requests.RequestException:
            pass
        time.sleep(0.2)
    raise RuntimeError(f'timeout waiting for {url}')


@pytest.mark.skip(reason='Bugged, to bo fixed')
def test_user_blocked_after_three_mentions_real_servers():
    # Ensure servers are up (adjust paths if your servers expose different health endpoints)
    _wait_for(f'{APP_BASE}/openapi.json')
    _wait_for(f'{MONGO_BASE}/openapi.json')

    # Ensure 'Foo' exists / has at least one block-counter row
    requests.post(f'{APP_BASE}/chat', json={'username': 'Foo', 'message': 'Hello world!'}, timeout=5.0)

    payload = {'username': 'Bar', 'message': 'Hi Foo'}

    # Three successful mentions
    for _ in range(3):
        r = requests.post(f'{APP_BASE}/chat', json=payload, timeout=5.0)
        assert r.status_code == 200
        data = r.json()
        assert 'reply' in data and data['reply'] is not None

    # Fourth attempt -> blocked
    r = requests.post(f'{APP_BASE}/chat', json=payload, timeout=5.0)
    assert r.status_code == 200
    data = r.json()
    assert data.get('reply') == BLOCKED_MESSAGE
