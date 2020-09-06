import enum
import logging.config
from typing import Any
from typing import Dict
from typing import IO
from typing import List
from typing import Optional
from typing import Union

import click

from ..loglevel import LogLevelDict

__all__ = ["ClickStyleFormatter", "ClickStreamHandler", "StreamMode"]

LogLevel = Union[str, int]

LEVEL_STYLES: LogLevelDict[Dict[str, Any]] = LogLevelDict(
    {
        logging.DEBUG: dict(fg="blue"),
        logging.INFO: dict(fg="green"),
        logging.WARNING: dict(fg="yellow"),
        logging.ERROR: dict(fg="red"),
    }
)


class ClickStyleFormatter(logging.Formatter):
    """
    Format log record attributes based on click style parameters.
    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = "%",
        level_styles: Optional[Dict[LogLevel, Dict[str, Any]]] = None,
        attributes: Optional[List[str]] = None,
    ) -> None:
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)
        self.level_styles = LogLevelDict(level_styles or LEVEL_STYLES)  # type: ignore
        self.attributes = attributes or ["levelname"]

    def apply_style_attributes(self, record: logging.LogRecord) -> logging.LogRecord:
        """
        Apply style attributes based on a log level.
        """
        for attribute in self.attributes:
            value = getattr(record, attribute)
            color_value = self.style_string(record.levelno, value)
            setattr(record, f"c{attribute}", color_value)
        return record

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a record for output
        """
        record = self.apply_style_attributes(record)
        return super().format(record)

    def style_string(self, level: LogLevel, message: str) -> str:
        """
        Style a message with the appropriate settings
        """
        style = self.level_styles.get(level, {})
        return click.style(message, **style)


class StreamMode(enum.Enum):
    STDOUT = "stdout"
    STDERR = "stderr"
    SPLIT = "split"


class ClickStreamHandler(logging.StreamHandler):
    def __init__(
        self, level: LogLevel = logging.NOTSET, mode: StreamMode = StreamMode.SPLIT, split: LogLevel = logging.INFO
    ) -> None:
        super().__init__()
        self.setLevel(level)

        stdout = click.get_text_stream("stdout")
        stderr = click.get_text_stream("stderr")

        streams: LogLevelDict[IO[str]]
        if mode == StreamMode.SPLIT:
            streams = LogLevelDict({split: stdout, logging.CRITICAL: stderr})
        elif mode == StreamMode.STDOUT:
            streams = LogLevelDict({logging.CRITICAL: stdout})
        elif mode == StreamMode.STDERR:
            streams = LogLevelDict({logging.CRITICAL: stderr})
        self.streams = streams

    def flush(self) -> None:
        """
        Flushes the stream.
        """
        self.acquire()
        try:
            for stream in self.streams.values():
                if hasattr(stream, "flush"):
                    stream.flush()
        finally:
            self.release()

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to determine how to do the
        output to the stream.
        """
        try:
            stream = self.streams[record.levelno]
            msg = self.format(record)
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

    @classmethod
    def from_format_and_settings(
        cls,
        level: LogLevel = logging.NOTSET,
        mode: StreamMode = StreamMode.SPLIT,
        split: LogLevel = logging.INFO,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = "%",
        level_styles: Optional[Dict[LogLevel, Dict[str, Any]]] = None,
        attributes: Optional[List[str]] = None,
    ) -> "ClickStreamHandler":
        """
        Set up a click stream handler and a click color formatter for logging.
        """
        formatter = ClickStyleFormatter(
            fmt=fmt, datefmt=datefmt, style=style, level_styles=level_styles, attributes=attributes
        )
        handler = cls(level=level, mode=mode, split=split)
        handler.setFormatter(formatter)
        return handler
