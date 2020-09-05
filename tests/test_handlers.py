import json
import logging
import uuid

import pytest

from flask_logging import ClickStyleFormatter
from flask_logging import JSONFormatter
from flask_logging import LogLevelDict


def test_loglevel_dict() -> None:

    lld: LogLevelDict[int] = LogLevelDict()
    assert not lld
    assert len(lld) == 0

    assert repr(lld).startswith("LogLevelDict")

    lld["INFO"] = 10

    assert lld["INFO"] == 10
    assert lld["DEBUG"] == 10
    assert list(lld) == [logging.INFO]

    assert "INFO" in lld
    assert "DEBUG" in lld
    assert "WARNING" not in lld

    lld["DEBUG"] = 5
    lld["WARNING"] = 8

    del lld["INFO"]
    assert "INFO" in lld
    assert lld["INFO"] == 8

    lld["DEBUG"] = 6
    assert lld["debug"] == 6
    with pytest.raises(KeyError):
        del lld["INFO"]


def test_formatter(record: logging.LogRecord) -> None:
    fmt = ClickStyleFormatter("[%(clevelname)s] %(msg)s")

    msg = fmt.format(record)

    # TODO Properly test that this message contains ANSI escape codes
    assert msg != f"[{logging.getLevelName(record.levelno)}] Some message here!"


def test_request_logging(client, watchlog):
    """Request logging should include the request ID"""
    rid = str(uuid.uuid4())

    _ = client.get("/", headers={"X-Request-ID": rid})
    record = watchlog.last("test-flask-logging.request")
    assert record.url == "/"
    assert record.method == "GET"
    assert record.response["status_code"] == 200
    assert record.request["id"] == rid


def test_request_log_jsonfmt(client, watchlog):
    """Logging should properly produce a nested JSON object with
    the custom JSON formatter"""
    _ = client.get("/")
    record = watchlog.last("test-flask-logging.request")

    formatter = JSONFormatter()
    data = json.loads(formatter.format(record))

    assert data["logger"]["name"] == "test-flask-logging.request"


def test_request_log_timing(client, watchlog):
    """Request logging should include request timing"""
    _ = client.get("/")
    record = watchlog.last("test-flask-logging.request")

    duration = record.response["request_duration"]

    assert isinstance(duration, float)
    assert duration > 0.0


def test_request_log_appinfo(client, watchlog):
    """Flask application info should be on the log record"""
    _ = client.get("/")
    record = watchlog.last("test-flask-logging.request")
    assert record.flask["environment"] == "test"
