from typing import Optional

from flask import Flask
from flask.signals import request_finished
from flask.signals import request_started

from .config import configure_logging
from .flask import FlaskAppInformation
from .flask import log_request
from .flask import log_response
from .flask import request_set_id
from .flask import request_track_time
from .flask import RequestInformation


class FlaskLogging:
    """
    Core Flask-Logging extension object.

    This class wraps several features of this extension in a re-usable, configurable package
    """

    def __init__(self, app: Optional[Flask] = None) -> None:
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:

        if app.config.get("FLASK_LOGGING_CONFIGURATION"):
            configure_logging(app.config["FLASK_LOGGING_CONFIGURATION"])

        if app.config.get("FLASK_LOGGING_REQUEST_ID"):
            request_set_id.init_app(app)

        if app.config.get("FLASK_LOGGING_REQUEST_DURATION"):
            request_track_time.init_app(app)

        if app.config.get("FLASK_LOGGING_REQUEST_FINISHED"):
            request_finished.connect(log_response, app)
        if app.config.get("FLASK_LOGGING_REUQEST_START"):
            request_started.connect(log_request, app)

        if app.config.get("FLASK_LOGGING_REQUEST_LOGGER"):
            logger_name = app.config.get("FLASK_LOGGING_REQUEST_LOGGER_NAME", "request")
            app.logger.getChild(logger_name).addFilter(RequestInformation())
            app.logger.getChild(logger_name).addFilter(FlaskAppInformation())
