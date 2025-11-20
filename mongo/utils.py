import os
import logging
from typing import Optional
from mongo.consts import MONGO_HOST_ENV, MONGO_PORT_ENV, MONGO_HOST_DEFAULT_VALUE, MONGO_PORT_DEFAULT_VALUE


logger = logging.getLogger("openai_ex.mongo.utils")


MONGO_BASE_URL: Optional[str] = None
_ACTUAL_HOST: Optional[str] = None
_ACTUAL_PORT: Optional[int] = None


def get_mongo_base_url():
    global MONGO_BASE_URL
    if not MONGO_BASE_URL:
        mongo_host = os.getenv(MONGO_HOST_ENV)
        mongo_port = os.getenv(MONGO_PORT_ENV)
        if mongo_host and mongo_port:
            _ACTUAL_HOST = mongo_host
            _ACTUAL_PORT = mongo_port
        else:
            # This is meant exclusively for dev mode, since mongo will probably not run on the same container
            logger.warning(f'Missing either {mongo_host=} or {mongo_port=}, falling back to defaults')
            _ACTUAL_HOST = MONGO_HOST_DEFAULT_VALUE
            _ACTUAL_PORT = MONGO_PORT_DEFAULT_VALUE
        MONGO_BASE_URL = 'http://%s:%s' % (_ACTUAL_HOST, _ACTUAL_PORT)
    return MONGO_BASE_URL


def get_mongo_host_port() -> tuple[str, int]:
    get_mongo_base_url()
    return _ACTUAL_HOST, _ACTUAL_PORT
