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
from typing import Optional
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


class JSONFormatter(logging.Formatter):
    """
    Format log records as JSON
    """

    converters: Dict[Union[Type, Tuple[Type]], Callable[[Any], Any]] = {
        dt.datetime: lambda value: value.isoformat(),
        dt.date: lambda value: f"{value:%Y-%m-%d}",
        HasSchema: lambda m: m.__schema__().dump(m),
        uuid.UUID: str,
        UserAgent: str,
        enum.Enum: lambda value: value.name,
        LocalProxy: repr,
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a record for output
        """
        ei = record.exc_info
        if ei:
            _ = super().format(record)  # just to get traceback text into record.exc_text
            record.exc_info = None  # to avoid Unpickleable error
        s = json.dumps(self._convert_json_data(record))
        if ei:
            record.exc_info = ei  # for next handler
        return s

    def _convert_json_value(self, value: Any, key: Optional[str] = None, logger: Optional[str] = None) -> Any:
        data: Any = None
        if isinstance(value, (str, int, float, bool, type(None))):
            data = value
        elif isinstance(value, (tuple, list)):
            data = [self._convert_json_value(v, key=f"{key}.<list>", logger=logger) for v in value]
        elif isinstance(value, dict):
            data = {k: self._convert_json_value(v, key=f"{key}.{k}", logger=logger) for k, v in value.items()}
        else:
            for clses, func in self.converters.items():
                if isinstance(value, clses):
                    data = func(value)
                    break
            else:
                warnings.warn(
                    JSONLogWarning(f"Unable to marshal type {type(value)} to JSON [key={key}, logger={logger}]")
                )
        return data

    def _convert_json_data(self, record: logging.LogRecord) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for key, value in record.__dict__.items():
            result = data[key] = self._convert_json_value(value, key=key, logger=record.name)
            if result is None and value is not None:
                warnings.warn(JSONLogWarning(f"Unable to marshal type {type(value)} for key {key} to JSON"))

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
