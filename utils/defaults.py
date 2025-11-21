import os
import logging
from typing import Optional, Any
from utils.consts import ENVIRONMENT_DEFAULTS


logger = logging.getLogger('openai_ex.utils.defaults')


def get_variable(name) -> Optional[Any]:
    os_value = os.getenv(name)
    if os_value is not None:
        return os_value
    default_value = ENVIRONMENT_DEFAULTS.get(name)
    if default_value is None:
        logger.warning(f'{name} missing default value in ENVIRONMENT_DEFAULTS')
    return default_value


def get_bool_env(name: str) -> bool:
    value = get_variable(name)
    if isinstance(value, bool):
        return value
    value_lower = value.lower()
    if value_lower in ('1', 'true', 'yes', 'on'):
        return True
    if value_lower in ('0', 'false', 'no', 'off'):
        return False
    return value
