import uuid

import pytest


@pytest.mark.parametrize("request_id", [str(uuid.uuid4()), "foo", None])
def test_response_logging(request_id, client, watchlog):
    """Request logging should include the request ID"""

    _ = client.get("/", headers={"X-Request-ID": request_id})
    record = watchlog.last("test-flask-logging.response")
    assert record.url == "/"
    assert record.method == "GET"
    assert record.response["status_code"] == 200
    assert record.request["id"] == str(request_id)  # request-id gets stringified


def test_request_logging_noop(app, watchlog):

    app.logger.getChild("request").info("A message here for testing")
    record = watchlog.last("test-flask-logging.request")

    assert record.url is None
    assert record.method is None


def test_response_log_timing(client, watchlog):
    """Response logging should include request timing"""
    _ = client.get("/")
    record = watchlog.last("test-flask-logging.response")

    duration = record.response["request_duration"]

    assert isinstance(duration, float)
    assert duration > 0.0


def test_request_log_appinfo(client, watchlog):
    """Flask application info should be on the log record"""
    _ = client.get("/")
    record = watchlog.last("test-flask-logging.request")
    assert record.flask["environment"] == "test"
