import json
import logging
import uuid
from typing import Any

import pytest
from flask_logging import ClickStyleFormatter
from flask_logging import JSONFormatter
from flask_logging import LogLevelDict


@pytest.fixture(params=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
def loglevel(request: Any) -> str:
    return request.param


@pytest.fixture
def record(loglevel: str) -> logging.LogRecord:
    return logging.LogRecord(
        name="test.log",
        level=getattr(logging, loglevel.upper()),
        pathname=__file__,
        lineno=10,
        msg="Some message here!",
        args=(),
        exc_info=None,
    )


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

    assert msg != f"[{logging.getLevelName(record.levelno)}] Some message here!"


def find_last_request_log(records, name="test-flask-logging.request"):
    for record in reversed(records):
        if record.name == name:
            return record
    else:  # pragma: no cover
        raise AssertionError("Request logging message not found!")


def test_request_logging(client, caplog):
    rid = str(uuid.uuid4())

    _ = client.get("/", headers={"X-Request-ID": rid})
    record = find_last_request_log(caplog.records)
    assert record.url == "/"
    assert record.method == "GET"
    assert record.response["status_code"] == 200
    assert record.request["id"] == rid


def test_request_log_jsonfmt(client, caplog):

    _ = client.get("/")
    record = find_last_request_log(caplog.records)

    formatter = JSONFormatter()
    data = json.loads(formatter.format(record))

    assert data["logger"]["name"] == "test-flask-logging.request"


def test_request_log_timing(client, caplog):

    _ = client.get("/")
    record = find_last_request_log(caplog.records)

    duration = record.response["request_duration"]

    assert isinstance(duration, float)
    assert duration > 0.0


def test_request_log_appinfo(client, caplog):

    _ = client.get("/")
    record = find_last_request_log(caplog.records)
    assert record.flask["environment"] == "test"
