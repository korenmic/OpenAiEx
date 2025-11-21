import os
import logging
from functools import lru_cache
from typing import Optional

from utils.consts import (
    MONGO_HOST_ENV,
    MONGO_PORT_ENV,
    AUTO_ACCEPT_NEW_USERS_ENV,
    MONGO_MAX_USERS_ENV,
)
from utils.defaults import get_variable, get_bool_env


logger = logging.getLogger('openai_ex.mongo.utils')


@lru_cache()
def get_auto_accept_new_users() -> bool:
    return get_bool_env(AUTO_ACCEPT_NEW_USERS_ENV)


@lru_cache()
def get_mongo_max_users() -> int:
    return int(get_variable(MONGO_MAX_USERS_ENV))


@lru_cache()
def get_mongo_base_url() -> Optional[str]:
    host, port = get_mongo_host_port()
    return 'http://%s:%s' % (host, port)


@lru_cache()
def get_mongo_host_port() -> tuple[Optional[str], Optional[int]]:
    return get_variable(MONGO_HOST_ENV), int(get_variable(MONGO_PORT_ENV))
