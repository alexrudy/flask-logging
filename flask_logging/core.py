from typing import Optional

from flask import Flask
from flask.signals import request_finished
from flask.signals import request_started

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
        request_set_id.init_app(app)
        request_track_time.init_app(app)

        request_finished.connect(log_response, app)
        request_started.connect(log_request, app)

        app.logger.getChild("request").addFilter(RequestInformation())
        app.logger.getChild("request").addFilter(FlaskAppInformation())
