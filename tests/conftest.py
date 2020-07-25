import pytest
from flask import Flask
from flask_logging.flask import init_app


@pytest.fixture
def app():
    test_app = Flask("test-flask-logging")
    test_app.env = "test"

    @test_app.route("/")
    def home():
        return "hello"

    yield test_app


@pytest.fixture
def client(app):
    init_app(app)
    with app.test_client() as c:
        yield c
