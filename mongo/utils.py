import os
import logging
from typing import Optional

from mongo.consts import (
    MONGO_HOST_ENV,
    MONGO_PORT_ENV,
    MONGO_HOST_DEFAULT_VALUE,
    MONGO_PORT_DEFAULT_VALUE,
    AUTO_ACCEPT_NEW_USERS_ENV,
    MONGO_MAX_USERS_ENV,
    AUTO_ACCEPT_NEW_USERS_DEFAULT,
    MONGO_MAX_USERS_DEFAULT,
)


logger = logging.getLogger('openai_ex.mongo.utils')


MONGO_BASE_URL: Optional[str] = None
_ACTUAL_HOST: Optional[str] = None
_ACTUAL_PORT: Optional[int] = None


def _get_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    value_lower = value.lower()
    if value_lower in ('1', 'true', 'yes', 'on'):
        return True
    if value_lower in ('0', 'false', 'no', 'off'):
        return False
    return default


def get_auto_accept_new_users() -> bool:
    return _get_bool_env(AUTO_ACCEPT_NEW_USERS_ENV, AUTO_ACCEPT_NEW_USERS_DEFAULT)


def get_mongo_max_users() -> int:
    value = os.getenv(MONGO_MAX_USERS_ENV)
    if value is None:
        return MONGO_MAX_USERS_DEFAULT
    try:
        return int(value)
    except ValueError:
        return MONGO_MAX_USERS_DEFAULT


def get_mongo_base_url() -> Optional[str]:
    global MONGO_BASE_URL
    global _ACTUAL_HOST
    global _ACTUAL_PORT
    if MONGO_BASE_URL is None:
        mongo_host = os.getenv(MONGO_HOST_ENV)
        mongo_port = os.getenv(MONGO_PORT_ENV)
        if mongo_host and mongo_port:
            _ACTUAL_HOST = mongo_host
            _ACTUAL_PORT = int(mongo_port)
        else:
            # This is meant exclusively for dev mode, since mongo will probably not run on the same container
            logger.warning(
                'Missing either mongo_host=%r or mongo_port=%r, falling back to defaults',
                mongo_host,
                mongo_port,
            )
            _ACTUAL_HOST = MONGO_HOST_DEFAULT_VALUE
            _ACTUAL_PORT = MONGO_PORT_DEFAULT_VALUE
        MONGO_BASE_URL = 'http://%s:%s' % (_ACTUAL_HOST, _ACTUAL_PORT)
    return MONGO_BASE_URL


def get_mongo_host_port() -> tuple[Optional[str], Optional[int]]:
    get_mongo_base_url()
    return _ACTUAL_HOST, _ACTUAL_PORT
