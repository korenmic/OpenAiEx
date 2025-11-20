import os
import sqlite3

from utils.schemas import UserStatus

DB_FILE_ENV = 'MONGO_DB_FILE'
DB_FILE_DEFAULT = os.path.join(os.path.dirname(__file__), 'mongo.db')


def get_db_path() -> str:
    """Return the path to the mongo database file.

    The value can be overridden via the MONGO_DB_FILE environment variable.
    """
    return os.getenv(DB_FILE_ENV, DB_FILE_DEFAULT)


def _user_status_columns() -> list[tuple[str, str, int]]:
    """Return a list of (name, sqlite_type, not_null) for UserStatus fields.

    This uses the Pydantic schema as the single source of truth so the
    table layout stays in sync with the Python model.
    """
    columns: list[tuple[str, str, int]] = []
    fields = UserStatus.__fields__
    for name, field in fields.items():
        python_type = field.type_
        if python_type is str:
            sqlite_type = 'TEXT'
        elif python_type is bool:
            sqlite_type = 'INTEGER'
        else:
            raise TypeError('Unsupported field %s with type %r' % (name, python_type))
        not_null = 0
        if not field.allow_none:
            not_null = 1
        columns.append((name, sqlite_type, not_null))
    return columns


def init_db() -> None:
    """Create the users table if it does not exist.

    The table definition is derived from the UserStatus Pydantic model.
    """
    db_path = get_db_path()
    directory = os.path.dirname(db_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    connection = sqlite3.connect(db_path)
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
        create_sql = 'CREATE TABLE IF NOT EXISTS users (%s)' % ', '.join(column_sql_parts)
        cursor.execute(create_sql)
        connection.commit()
    finally:
        connection.close()
