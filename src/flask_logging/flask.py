import logging.config
import time
import uuid
from typing import Any
from typing import Dict

from flask import current_app
from flask import Flask
from flask import g
from flask import has_app_context
from flask import has_request_context
from flask import request
from flask import Response

from .request_context import request_context_manger
from .request_context import RequestContextGenerator

__all__ = ["FlaskAppInformation", "RequestInformation", "log_request", "log_response"]


class FlaskAppInformation(logging.Filter):
    """
    Add information about the flask app and configuration
    """

    def filter(self, log_record: Any) -> bool:
        if has_app_context():
            log_record.flask = dict(
                environment=current_app.env, instance_path=current_app.instance_path, name=current_app.name
            )
        return True


class RequestInformation(logging.Filter):
    """
    Add request information to log records
    """

    def filter(self, log_record: Any) -> bool:
        """Enrich log records with request infomration"""
        if has_request_context():

            log_record.request = {
                "path": request.path,
                "method": request.method,
                "remote_addr": request.remote_addr,
                "user_agent": request.user_agent,
            }
            if "SERVER_PROTOCOL" in request.environ:
                log_record.request["protocol"] = request.environ["SERVER_PROTOCOL"]

            if hasattr(g, "request_id"):
                log_record.request["id"] = g.request_id

            log_record.url = request.path
            log_record.method = request.method
            log_record.remote_addr = request.remote_addr

        else:
            log_record.request = {}
            log_record.url = None
            log_record.method = None
            log_record.remote_addr = None

        return True


def log_request(sender: Flask, **extra: Any) -> None:
    """
    Log the start of a request to a flask app.
    """
    logger_name = sender.config.get("FLASK_LOGGING_REQUEST_LOGGER_NAME", "request")

    logger = sender.logger.getChild(logger_name)
    logger.debug(f"{request.method} {request.url} BEGIN", extra={"event": "request_started"})


def log_response(sender: Flask, response: Response, **extra: Any) -> None:
    """
    Log a response form the app.

    Should be attached to the `request_finished` signal.
    """
    logger_name = sender.config.get("FLASK_LOGGING_RESPONSE_LOGGER_NAME", "response")
    logger = sender.logger.getChild(logger_name)

    response_keywords: Dict[str, Any] = {}
    response_keywords["status"] = response.status
    response_keywords["status_code"] = response.status_code
    response_keywords["content_type"] = response.content_type

    content_length = response.content_length
    if content_length is not None:
        response_keywords["content_length"] = content_length

    if "_request_duration" in g:
        response_keywords["request_duration"] = g._request_duration

    logger.info(f"{response.status}", extra=dict(response=response_keywords, event="request_finished"))


@request_context_manger
def request_set_id() -> RequestContextGenerator:
    """
    Set a UUID in the header for each request.
    """

    request_header = current_app.config.get("FLASK_LOGGING_REQUEST_ID_HEADER", "X-Request-ID")

    request_id = request.headers.get(request_header, None)
    if request_id is None:
        request_id = str(uuid.uuid4())

    g.setdefault("request_id", request_id)
    response = yield
    response.headers.setdefault(request_header, g.get("request_id", request_id))
    return response


@request_context_manger
def request_track_time() -> RequestContextGenerator:
    """
    Track the duration of each request.
    """
    start_time = time.monotonic()
    response = yield
    duration = time.monotonic() - start_time
    g._request_duration = duration
    return response
