import dataclasses as dc
import logging
from pathlib import Path
from typing import Any
from typing import Iterator
from typing import List

import pytest
from _pytest.logging import LogCaptureFixture
from flask import Flask
from flask.testing import FlaskClient

from flask_logging import FlaskLogging


@pytest.fixture
def app() -> Iterator[Flask]:
    test_app = Flask("test-flask-logging")
    test_app.env = "test"

    test_cfg = Path(__file__).parent / "configuration.cfg"
    test_app.config.from_pyfile(test_cfg)

    @test_app.route("/")
    def home():
        return "hello"

    yield test_app


@pytest.fixture
def client(app: Flask) -> Iterator[FlaskClient]:
    extension = FlaskLogging()
    extension.init_app(app)
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
        raise AssertionError(f"Log message for {logger} not found!")  # pragma: nocover

    def filter(self, logger: str) -> List[logging.LogRecord]:
        return [record for record in self.caplog.records if record.name == logger]


@pytest.fixture
def timestamp():
    return 1599335372


@pytest.fixture
def watchlog(caplog: LogCaptureFixture) -> Iterator[LogWatcher]:
    yield LogWatcher(caplog)


@pytest.fixture(params=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
def loglevel(request: Any) -> str:
    return request.param


@pytest.fixture
def record(loglevel: str, timestamp: int) -> logging.LogRecord:
    r = logging.LogRecord(
        name="test.log",
        level=getattr(logging, loglevel.upper()),
        pathname=__file__,
        lineno=10,
        msg="Some message here!",
        args=(),
        exc_info=None,
    )

    r.created = timestamp
    r.msecs = 295
    r.relativeCreated = timestamp - 62

    return r
