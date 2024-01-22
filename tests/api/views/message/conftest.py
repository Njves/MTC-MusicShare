import pytest
from flask_login import FlaskLoginClient
from werkzeug.datastructures import Headers

from app import create_app
from tests.config import TestConfig


@pytest.fixture(scope="session")
def app():
    """Set up global front-end app for functional tests

    Initialized once per test-run
    """
    app = create_app(TestConfig)
    app.app_context().push()
    app.test_client_class = FlaskLoginClient
    yield app
