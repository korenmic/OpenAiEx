import sqlite3

from mongo import db as mongo_db
from mongo.consts import USERS_TABLE_NAME
from utils.consts import MONGO_DB_FILE_ENV
from utils.schemas import UserStatus

_TEST_USERS_DB = 'test_users.db'

def test_init_db_creates_users_table(tmp_path, monkeypatch):
    db_path = tmp_path / _TEST_USERS_DB
    monkeypatch.setenv(MONGO_DB_FILE_ENV, str(db_path))

    mongo_db.init_db()

    assert db_path.exists()

    connection = sqlite3.connect(str(db_path))
    try:
        cursor = connection.cursor()
        cursor.execute('PRAGMA table_info(%s)' % USERS_TABLE_NAME)
        rows = cursor.fetchall()
    finally:
        connection.close()

    # rows: cid, name, type, notnull, dflt_value, pk
    columns = {row[1]: row[2] for row in rows}
    assert columns.get('username') == 'TEXT'
    assert columns.get('blocked') == 'INTEGER'

    # Ensure schema stayed in sync with the Pydantic model.
    model_fields = set(UserStatus.model_fields.keys())
    assert set(columns.keys()) == model_fields
