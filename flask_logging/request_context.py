import dataclasses as dc
from typing import Any
from typing import Callable
from typing import cast
from typing import Dict
from typing import Generator
from typing import Optional
from weakref import WeakKeyDictionary

from flask import current_app
from flask import Flask
from flask import Response

__all__ = ["RequestContextWrapper", "request_context_manger"]

RequestContextGenerator = Generator[Any, Response, Optional[Response]]
RequestContextFunction = Callable[[], RequestContextGenerator]
_ContextWrappers = Dict["RequestContextWrapper", RequestContextGenerator]

EXTENSION_NAME = "flask_login.request_context"


@dc.dataclass
class _RequestContextState:
    context_wrappers: _ContextWrappers = dc.field(default_factory=lambda: cast(_ContextWrappers, WeakKeyDictionary()))


class RequestContextWrapper:
    """
    Decorator to set up a single generator function as a request wrapper.

    The generator will be sent the response at the end of the request, so it should yield
    at the point it would like the request to process.

    A minimal use::

        @RequestContextWrapper
        def request_track_time() -> RequestContextGenerator:
            start_time = time.monotonic()
            response = yield
            duration = time.monotonic() - start_time
            response.headers['X-Request-Duration'] = duration
            return response

    Parameters
    ----------
    context_function: callable generator
        Generator used for the request context.

    """

    def __init__(self, context_function: RequestContextFunction, app: Optional[Flask] = None) -> None:

        self.context = context_function
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.extensions[EXTENSION_NAME] = _RequestContextState()

    def _get_state(self) -> _RequestContextState:
        try:
            if current_app:
                return current_app._get_current_object().extensions[EXTENSION_NAME]

            if self.app is not None:
                return self.app.extensions[EXTENSION_NAME]
        except KeyError:
            raise RuntimeError(
                "The request context extension was not registered to the current "
                "application.  Please make sure to call init_app() first."
            )

        raise RuntimeError("No application found. Either work inside a view function or push an application context")

    def _before_request(self) -> None:

        ctx = self.context()
        try:
            next(ctx)
        except StopIteration as e:
            raise RuntimeError("Generator did not yield") from e
        else:
            state = self._get_state()
            state.context_wrappers[self] = ctx

    def _after_request(self, response: Response) -> Response:
        state = self._get_state()

        try:
            ctx = state.context_wrappers.pop(self)
        except KeyError:
            # Can't find this context, so we don't modify the response and just return it here.
            return response

        try:
            ctx.send(response)
        except StopIteration as e:
            if isinstance(e.value, Response):
                response = e.value
            elif e.value is not None:
                raise RuntimeError(f"Generator returned something which is not a response: {type(e.value)}")
        else:
            raise RuntimeError("Generator did not stop")
        return response


def request_context_manger(f: RequestContextFunction) -> RequestContextWrapper:
    """
    Mark this function as a request context manager
    """
    return RequestContextWrapper(f, app=None)
