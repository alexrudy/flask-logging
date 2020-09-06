import abc
import datetime as dt
import enum
import json
import logging.config
import uuid
import warnings
from typing import Any
from typing import Callable
from typing import Dict
from typing import Tuple
from typing import Type
from typing import Union

from werkzeug.local import LocalProxy
from werkzeug.useragents import UserAgent


__all__ = ["JSONLogWarning", "JSONFormatter"]


class JSONLogWarning(Warning):
    """Warning used when an unmarshallable type is being logged"""


class HasSchema(abc.ABC):
    @classmethod
    def __subclasshook__(cls: Type["HasSchema"], C: Type) -> bool:
        if cls is HasSchema:
            if any("__schema__" in B.__dict__ for B in C.__mro__):
                return True
        return NotImplemented


class FlexJSONEncoder(json.JSONEncoder):
    """Flexible JSON encoder for use with more JSON types"""

    converters: Dict[Union[Type, Tuple[Type]], Callable[[Any], Any]] = {
        dt.datetime: lambda value: value.isoformat(),
        dt.date: lambda value: f"{value:%Y-%m-%d}",
        HasSchema: lambda m: m.__schema__().dump(m),
        uuid.UUID: str,
        UserAgent: str,
        enum.Enum: lambda value: value.name,
        LocalProxy: repr,
    }

    def default(self, obj: Any) -> Any:
        for clses, func in self.converters.items():
            if isinstance(obj, clses):
                return func(obj)
        else:
            warnings.warn(JSONLogWarning(f"Unable to marshal type {type(obj)} to JSON"))
            return f"<Unecodeable type: {type(obj)!r} {obj!r}>"
        return super().default(obj)


class JSONFormatter(logging.Formatter):
    """
    Format log records as JSON
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a record for output
        """
        ei = record.exc_info
        if ei:
            _ = super().format(record)  # just to get traceback text into record.exc_text
            record.exc_info = None  # to avoid Unpickleable error
        s = json.dumps(self._convert_json_data(record), sort_keys=True, cls=FlexJSONEncoder)
        if ei:
            record.exc_info = ei  # for next handler
        return s

    def _convert_json_data(self, record: logging.LogRecord) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        data.update(record.__dict__)

        data["message"] = {"text": data.pop("msg"), "args": data.pop("args")}

        data["timing"] = {
            "ascii": data.pop("asctime", None),
            "created": data.pop("created"),
            "msecs": data.pop("msecs"),
            "relativeCreated": data.pop("relativeCreated"),
        }

        data["python"] = {
            "code": {
                "path": data.pop("pathname"),
                "filename": data.pop("filename"),
                "module": data.pop("module"),
                "lineno": data.pop("lineno"),
                "funcName": data.pop("funcName"),
            },
            "stack": data.pop("stack_info"),
            "exc": {"info": data.pop("exc_info"), "text": data.pop("exc_text")},
            "thread": {"name": data.pop("threadName"), "id": data.pop("thread")},
            "process": {"name": data.pop("processName"), "pid": data.pop("process")},
        }
        data["logger"] = {
            "name": data.pop("name"),
            "level": {
                "number": data.pop("levelno"),
                "name": data.pop("levelname"),
                "ansiname": data.pop("clevelname", None),
            },
        }

        return data
