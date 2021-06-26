import json
import logging
import warnings

from flask_logging.handlers.json import JSONFormatter
from flask_logging.handlers.json import JSONLogWarning
from flask_logging.handlers.json import makeLogRecordfromJson


def test_request_log_jsonfmt(client, watchlog):
    """Logging should properly produce a nested JSON object with
    the custom JSON formatter"""
    _ = client.get("/")
    record = watchlog.last("test-flask-logging.response")

    formatter = JSONFormatter()
    data = json.loads(formatter.format(record))

    assert data["logger"]["name"] == "test-flask-logging.response"
    assert data["message"] == "200 OK"


def test_log_jsonfmt_exc_info(watchlog):
    tlogger = logging.getLogger("test-json-logging")

    try:
        raise ValueError("Some value error")
    except ValueError:
        tlogger.exception("Caught some error")

    record = watchlog.last("test-json-logging")

    formatter = JSONFormatter()
    data = json.loads(formatter.format(record))

    assert data["python"]["exc"]["text"] is not None


def test_log_jsonfmt_warning(record, recwarn):
    warnings.simplefilter("always")

    record.my_attr = object()  # Something we can't convert to JSON

    formatter = JSONFormatter()
    data = json.loads(formatter.format(record))
    assert "my_attr" in data

    assert len(recwarn) == 1
    warning = recwarn.pop(JSONLogWarning)
    assert str(warning.message) == "Unable to marshal type <class 'object'> to JSON"


def test_log_jsonfmt_roundtrip(record):
    formatter = JSONFormatter()
    data = formatter.format(record)

    rt_record = makeLogRecordfromJson(data)

    for key, expected in record.__dict__.items():
        value = rt_record.__dict__[key]

        assert value == expected


class MockSchema:
    def dump(self, obj):
        return obj.__class__.__name__


class MockObjWithSchema:

    __schema__ = MockSchema


def test_log_jsonfmt_schema(record, recwarn):
    warnings.simplefilter("always")

    record.my_attr = MockObjWithSchema()  # Something which uses implicit-style marshmallow schemas

    formatter = JSONFormatter()
    data = json.loads(formatter.format(record))
    assert data["my_attr"] == "MockObjWithSchema"
    assert len(recwarn) == 0
