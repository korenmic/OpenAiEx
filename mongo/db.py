import os
import sqlite3
from functools import lru_cache
from typing import get_args

from utils.consts import CLEAR_DB_ENV, ENVIRONMENT_DEFAULTS, MONGO_DB_FILE_ENV, USERS_TABLE_NAME
from utils.defaults import get_variable, get_bool_env
from utils.schemas import UserStatus


@lru_cache()
def get_db_path() -> str:
    """Return the path to the mongo database file.

    The value can be overridden via the MONGO_DB_FILE environment variable.
    """
    return get_variable(MONGO_DB_FILE_ENV)


def _user_status_columns() -> list[tuple[str, str, int]]:
    """Return a list of (name, sqlite_type, not_null) for UserStatus fields.

    This uses the Pydantic schema as the single source of truth so the
    table layout stays in sync with the Python model.
    """
    columns: list[tuple[str, str, int]] = []
    fields = UserStatus.model_fields
    for name, field in fields.items():
        python_type = field.annotation
        if python_type is str:
            sqlite_type = 'TEXT'
        elif python_type is bool:
            sqlite_type = 'INTEGER'
        else:
            raise TypeError('Unsupported field %s with type %r' % (name, python_type))
        not_null = 0
        field_supports_none = type(None) in get_args(field.annotation) or field.default is None
        if not field_supports_none:
            not_null = 1
        columns.append((name, sqlite_type, not_null))
    return columns


def _init_path() -> None:
    db_path = get_db_path()
    directory = os.path.dirname(db_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    if get_bool_env(CLEAR_DB_ENV) and os.path.exists(db_path):
        os.remove(db_path)


def _get_connection() -> sqlite3.Connection:
    return sqlite3.connect(get_db_path())


def init_db() -> None:
    """Create the users table if it does not exist.

    The table definition is derived from the UserStatus Pydantic model.
    """
    _init_path()

    connection = _get_connection()
    try:
        cursor = connection.cursor()
        columns = _user_status_columns()
        column_sql_parts = []
        for name, sqlite_type, not_null in columns:
            parts = [name, sqlite_type]
            if not_null:
                parts.append('NOT NULL')
            if name == 'username':
                parts.append('PRIMARY KEY')
            column_sql_parts.append(' '.join(parts))
        create_sql = 'CREATE TABLE IF NOT EXISTS %s (%s)' % (
            USERS_TABLE_NAME,
            ', '.join(column_sql_parts),
        )
        cursor.execute(create_sql)
        connection.commit()
    finally:
        connection.close()


def list_usernames() -> list[str]:
    connection = _get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT username FROM %s' % USERS_TABLE_NAME)
        rows = cursor.fetchall()
    finally:
        connection.close()
    return [row[0] for row in rows]
