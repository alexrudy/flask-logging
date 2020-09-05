import logging

import pytest

from flask_logging.handlers.common import CommonLogFormat


def test_formatter_empty(record: logging.LogRecord) -> None:
    """Test an undecorated log message"""
    fmt = CommonLogFormat()

    msg = fmt.format(record)

    assert msg == '- - - [05/Sep/2020 12:49:32] "- - -" - -'


@pytest.fixture
def request_record(record: logging.LogRecord) -> logging.LogRecord:
    record.request = {"path": "/", "remote_addr": "127.0.0.1", "method": "GET", "protocol": "HTTP/1.1"}  # type: ignore
    return record


def test_formatter_request(request_record: logging.LogRecord) -> None:
    fmt = CommonLogFormat()

    msg = fmt.format(request_record)

    assert msg == '127.0.0.1 - - [05/Sep/2020 12:49:32] "GET / HTTP/1.1" - -'
