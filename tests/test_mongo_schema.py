import sqlite3

from mongo import db as mongo_db
from utils.schemas import UserStatus


def test_init_db_creates_users_table(tmp_path, monkeypatch):
    db_path = tmp_path / 'test_users.db'
    monkeypatch.setenv('MONGO_DB_FILE', str(db_path))

    mongo_db.init_db()

    assert db_path.exists()

    connection = sqlite3.connect(str(db_path))
    try:
        cursor = connection.cursor()
        cursor.execute('PRAGMA table_info(users)')
        rows = cursor.fetchall()
    finally:
        connection.close()

    # rows: cid, name, type, notnull, dflt_value, pk
    columns = {row[1]: row[2] for row in rows}
    assert columns.get('username') == 'TEXT'
    assert columns.get('blocked') == 'INTEGER'

    # Ensure schema stayed in sync with the Pydantic model.
    model_fields = set(UserStatus.__fields__.keys())
    assert set(columns.keys()) == model_fields
