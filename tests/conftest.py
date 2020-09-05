import dataclasses as dc
import logging
from typing import Any
from typing import Iterator

import pytest
from _pytest.logging import LogCaptureFixture
from flask import Flask
from flask.testing import FlaskClient

from flask_logging.flask import init_app


@pytest.fixture
def app() -> Iterator[Flask]:
    test_app = Flask("test-flask-logging")
    test_app.env = "test"

    @test_app.route("/")
    def home():
        return "hello"

    yield test_app


@pytest.fixture
def client(app: Flask) -> Iterator[FlaskClient]:
    init_app(app)
    with app.test_client() as c:
        yield c


@dc.dataclass
class LogWatcher:
    """A custom log capturing utility which can automatically filter things"""

    caplog: LogCaptureFixture

    def last(self, logger: str) -> logging.LogRecord:
        for record in reversed(self.caplog.records):
            if record.name == logger:
                return record
        raise AssertionError("Request logging message not found!")


@pytest.fixture
def watchlog(caplog: LogCaptureFixture) -> Iterator[LogWatcher]:
    yield LogWatcher(caplog)


@pytest.fixture(params=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
def loglevel(request: Any) -> str:
    return request.param


@pytest.fixture
def record(loglevel: str) -> logging.LogRecord:
    r = logging.LogRecord(
        name="test.log",
        level=getattr(logging, loglevel.upper()),
        pathname=__file__,
        lineno=10,
        msg="Some message here!",
        args=(),
        exc_info=None,
    )

    r.created = 1599335372
    r.msecs = 295
    r.relativeCreated = 1599335370

    return r
