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


LOG_RECORD_SCHEMA: Dict[str, Tuple[str, ...]] = {
    "message": ("message",),
    "msg": ("message_info", "text"),
    "args": ("message_info", "args"),
    "asctime": ("timing", "ascii"),
    "created": ("timing", "created"),
    "msecs": ("timing", "msecs"),
    "relativeCreated": ("timing", "relativeCreated"),
    "pathname": ("python", "code", "pathname"),
    "filename": ("python", "code", "filename"),
    "module": ("python", "code", "module"),
    "lineno": ("python", "code", "lineno"),
    "funcName": ("python", "code", "funcname"),
    "stack_info": ("python", "stack"),
    "exc_info": ("python", "exc", "info"),
    "exc_text": ("python", "exc", "text"),
    "threadName": ("python", "thread", "name"),
    "thread": ("python", "thread", "id"),
    "process": ("python", "process", "pid"),
    "processName": ("python", "process", "name"),
    "name": ("logger", "name"),
    "levelno": ("logger", "level", "number"),
    "levelname": ("logger", "level", "name"),
    "clevelname": ("logger", "level", "ansiname"),
}


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

        raw = dict(record.__dict__)

        for key, value in raw.items():
            *parents, target_key = LOG_RECORD_SCHEMA.get(key, (key,))
            target = data
            for parent in parents:
                target = target.setdefault(parent, {})
            target[target_key] = value

        return data


def makeLogRecordfromJson(data: str) -> logging.LogRecord:
    raw = json.loads(data)
    recordinfo = {**raw}

    if isinstance(raw.get("message", None), dict):
        message = raw.pop("message")
        if "message_info" not in raw:
            raw["message_info"] = message
        else:
            raw["message_original"] = message

    # This will duplicate standard keys – i.e. it doesn't
    # remove the nested ones, but thats probably fine?
    for key, position in LOG_RECORD_SCHEMA.items():

        *parents, target_key = position
        target = raw
        for parent in parents:
            target = target.get(parent, {})

        if target_key in target:
            recordinfo[key] = target[target_key]

    if "args" in recordinfo:
        recordinfo["args"] = tuple(recordinfo["args"])

    if "message" in recordinfo and "msg" not in recordinfo:
        recordinfo["msg"] = recordinfo["message"]
        recordinfo["args"] = None

    return logging.makeLogRecord(recordinfo)
