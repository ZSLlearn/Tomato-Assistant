import os
import tempfile
import pytest
from app import create_app
from app.database import get_db, init_db


@pytest.fixture
def app():
    """Integration test fixture: app with temp file database."""
    import config
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    config.DATABASE = db_path
    app = create_app()
    app.config['TESTING'] = True
    yield app
    try:
        os.unlink(db_path)
    except PermissionError:
        pass  # Windows file lock, cleanup will happen on next reboot


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db():
    """Unit test fixture: independent in-memory db with tables."""
    import config
    config.DATABASE = ":memory:"
    conn = get_db()
    init_db(conn=conn)
    yield conn
    conn.close()
