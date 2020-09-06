import pytest
from flask import Flask
from flask import Response

from flask_logging.request_context import request_context_manger
from flask_logging.request_context import RequestContextGenerator
from flask_logging.request_context import RequestContextWrapper


def test_simple_context(app: Flask) -> None:
    """Test a basic, do nothing context"""

    sections = []

    @request_context_manger
    def request_dummy_context() -> RequestContextGenerator:
        """
        Set a UUID in the header for each request.
        """
        nonlocal sections
        sections.append("before-request")

        response = yield
        sections.append("after-request")
        assert isinstance(response, Response)

        return response

    request_dummy_context.init_app(app)

    with pytest.raises(RuntimeError):
        _ = request_dummy_context._get_state()

    with app.test_client() as client:
        response = client.get("/")
    assert response.status_code == 200

    assert sections == ["before-request", "after-request"]


def test_bad_response_context(app: Flask) -> None:
    """Test a basic, do nothing context"""

    sections = []

    @request_context_manger
    def request_dummy_context() -> RequestContextGenerator:
        """
        Set a UUID in the header for each request.
        """
        nonlocal sections
        sections.append("before-request")

        response = yield
        sections.append("after-request")
        assert isinstance(response, Response)

        return "hello"  # type: ignore

    request_dummy_context.init_app(app)

    with app.test_client() as client:
        response = client.get("/")
    assert response.status_code == 500

    assert sections == ["before-request", "after-request"]


def test_not_a_generator(app: Flask) -> None:

    sections = []

    @request_context_manger
    def request_dummy_context() -> RequestContextGenerator:
        """
        Set a UUID in the header for each request.
        """
        nonlocal sections
        sections.append("before-request")

        while False:
            yield

        return None

    request_dummy_context.init_app(app)

    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 500

    assert sections == ["before-request"]


def test_infinite_generator(app: Flask) -> None:

    sections = []

    @request_context_manger
    def request_dummy_context() -> RequestContextGenerator:
        """
        Set a UUID in the header for each request.
        """
        nonlocal sections
        sections.append("before-request")

        while True:
            yield

    request_dummy_context.init_app(app)

    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 500

    assert sections == ["before-request"]


def request_dummy_generator() -> RequestContextGenerator:
    """
    Set a UUID in the header for each request.
    """
    response = yield
    assert isinstance(response, Response)
    return response


def test_not_appctx(app: Flask) -> None:

    request_dummy_context = RequestContextWrapper(request_dummy_generator, app)

    state = request_dummy_context._get_state()
    assert not state.context_wrappers

    with app.test_client() as client:
        response = client.get("/")
    assert response.status_code == 200


def test_wrong_app(app: Flask) -> None:

    wrong_app = Flask(__name__)
    request_dummy_context = RequestContextWrapper(request_dummy_generator, wrong_app)

    with app.app_context():
        with pytest.raises(RuntimeError):
            request_dummy_context._get_state()
