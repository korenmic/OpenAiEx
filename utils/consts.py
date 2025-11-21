import logging
from pathlib import Path

# Environment variable keys

# Values should be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL.
# TODO - convert into Enum
OPENAIEX_LOG_LEVEL_FILE_ENV = 'OPENAIEX_LOG_LEVEL_FILE'
OPENAIEX_LOG_LEVEL_STDOUT_ENV = 'OPENAIEX_LOG_LEVEL_STDOUT'

MONGO_HOST_ENV = 'MONGO_SERVICE_HOST'
MONGO_PORT_ENV = 'MONGO_SERVICE_PORT'
MONGO_DB_FILE_ENV = 'MONGO_DB_FILE'
APP_RELOAD_ENV = 'APP_RELOAD'

AUTO_ACCEPT_NEW_USERS_ENV = 'AUTO_ACCEPT_NEW_USERS'
MONGO_MAX_USERS_ENV = 'MONGO_MAX_USERS'
CLEAR_DB_ENV = 'CLEAR_DB'

# Central place for environment defaults. Keys are env var names.
ENVIRONMENT_DEFAULTS = {
    OPENAIEX_LOG_LEVEL_FILE_ENV: 'DEBUG',
    OPENAIEX_LOG_LEVEL_STDOUT_ENV: 'INFO',
    MONGO_HOST_ENV: '127.0.0.1',
    MONGO_PORT_ENV: 8001,
    MONGO_DB_FILE_ENV: Path(__file__).resolve().parent / 'mongo.db',
    APP_RELOAD_ENV: 'false',
    CLEAR_DB_ENV: 'true',
    AUTO_ACCEPT_NEW_USERS_ENV: True,
    MONGO_MAX_USERS_ENV: 100
}


# None-Environment consts
BLOCKED_MESSAGE = 'Your user is currently blocked, contact support to release the block'
USERS_TABLE_NAME = 'users'
BLOCK_COUNTER_THRESHOLD = 3
