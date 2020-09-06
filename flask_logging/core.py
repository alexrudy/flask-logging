import logging
import os
from typing import Optional

import pkg_resources
from flask import Config
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

    def add_flask_filters(self, logger: logging.Logger) -> None:
        if not any(isinstance(f, RequestInformation) for f in logger.filters):
            logger.addFilter(RequestInformation())
        if not any(isinstance(f, FlaskAppInformation) for f in logger.filters):
            logger.addFilter(FlaskAppInformation())

    def set_defaults(self, app: Flask) -> None:
        default_filename = os.path.abspath(pkg_resources.resource_filename(__name__, "defaults.cfg"))
        defaults = Config(root_path="/dev/null")
        defaults.from_pyfile(default_filename)
        for key, value in defaults.items():
            app.config.setdefault(key, value)

    def init_app(self, app: Flask) -> None:
        self.set_defaults(app)

        if app.config.get("FLASK_LOGGING_CONFIGURATION"):
            configure_logging(app.config["FLASK_LOGGING_CONFIGURATION"])

        if app.config.get("FLASK_LOGGING_REQUEST_ID"):
            request_set_id.init_app(app)

        if app.config.get("FLASK_LOGGING_REQUEST_DURATION"):
            request_track_time.init_app(app)

        if app.config.get("FLASK_LOGGING_REQUEST_FINISHED"):
            request_finished.connect(log_response, app)
        if app.config.get("FLASK_LOGGING_REQUEST_STARTED"):
            request_started.connect(log_request, app)

        if app.config.get("FLASK_LOGGING_REQUEST_LOGGER"):
            logger_name = app.config.get("FLASK_LOGGING_REQUEST_LOGGER_NAME", "request")
            self.add_flask_filters(app.logger.getChild(logger_name))

        if app.config.get("FLASK_LOGGING_RESPONSE_LOGGER"):
            logger_name = app.config.get("FLASK_LOGGING_RESPONSE_LOGGER_NAME", "response")
            self.add_flask_filters(app.logger.getChild(logger_name))
