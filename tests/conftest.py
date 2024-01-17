import pytest
from flask_login import FlaskLoginClient

from app import create_app, db as database
from tests.config import TestConfig


@pytest.fixture(scope="session")
def app():
    """Global skylines application fixture

    Initialized with testing config file.
    """
    app = create_app(TestConfig)
    app.app_context().push()
    yield app

@pytest.fixture(scope="session")
def db(app):
    """Creates clean database schema and drops it on teardown

    Note, that this is a session scoped fixture, it will be executed only once
    and shared among all tests. Use `db_session` fixture to get clean database
    before each test.
    """
    database.create_all()
    yield db
    database.session.remove()
    database.drop_all()

@pytest.fixture(scope="function")
def db_session(db, app):
    """Provides clean database before each test. After each test,
    session.rollback() is issued.

    Return sqlalchemy session.
    """
    for table in reversed(database.metadata.sorted_tables):
        database.session.execute(table.delete())
    yield database.session
    database.session.rollback()
