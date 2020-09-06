import logging
from typing import Any

import pytest
from flask import Flask

from flask_logging.flask import init_app
from flask_logging.handlers.common import CommonLogFormat


def test_formatter_empty(record: logging.LogRecord) -> None:
    """Test an undecorated log message"""
    fmt = CommonLogFormat()

    msg = fmt.format(record)

    assert msg == '- - - [05/Sep/2020 19:49:32] "- - -" - -'


@pytest.fixture
def request_record(record: logging.LogRecord) -> logging.LogRecord:
    record.request = {"path": "/", "remote_addr": "127.0.0.1", "method": "GET", "protocol": "HTTP/1.1"}  # type: ignore
    return record


def test_formatter_request(request_record: logging.LogRecord) -> None:
    fmt = CommonLogFormat()

    msg = fmt.format(request_record)

    assert msg == '127.0.0.1 - - [05/Sep/2020 19:49:32] "GET / HTTP/1.1" - -'


@pytest.fixture
def response_record(request_record: logging.LogRecord) -> logging.LogRecord:
    request_record.response = {"status_code": 200, "content_length": 1234}  # type: ignore
    return request_record


def test_formatter_response(response_record: logging.LogRecord) -> None:
    fmt = CommonLogFormat()

    msg = fmt.format(response_record)

    assert msg == '127.0.0.1 - - [05/Sep/2020 19:49:32] "GET / HTTP/1.1" 200 1234'


def test_response_live_app(app: Flask, watchlog: Any, timestamp: int) -> None:
    """Test response logging on a live app"""
    app.config["FLASK_LOGGING_RESPONSE_LOGGER_NAME"] = "test-response-logger"
    init_app(app)

    with app.test_client() as client:
        _ = client.get("/")

    record = watchlog.last("test-flask-logging.test-response-logger")
    assert hasattr(record, "request")
    assert hasattr(record, "response")

    record.created = timestamp
    fmt = CommonLogFormat()

    message = fmt.format(record)

    assert message == '127.0.0.1 - - [05/Sep/2020 19:49:32] "GET / HTTP/1.1" 200 5'
