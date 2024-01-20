import json

import pytest
from flask import Response
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
    app.response_class = ApiResponse
    yield app

class ApiClient(FlaskLoginClient):
    def open(self, *args, **kwargs):
        headers = kwargs.pop("headers", Headers())
        headers.setdefault("User-Agent", "py.test")
        kwargs["headers"] = headers

        json_data = kwargs.pop("json", None)
        if json_data is not None:
            kwargs["data"] = json.dumps(json_data)
            kwargs["content_type"] = "application/json"
        return super(FlaskLoginClient, self).open(*args, **kwargs)


class ApiResponse(Response):
    @property
    def json(self):
        return json.loads(self.data)

@pytest.fixture(scope="session")
def client(app):
    """Set up global front-end app for functional tests

    Initialized once per test-run
    """
    yield app.test_client()