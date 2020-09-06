import datetime as dt
import logging
from collections import defaultdict
from typing import DefaultDict


class CommonLogFormat(logging.Formatter):
    """Python standard logging formatter which matches the common log format which is the default for apache webservers.
    """

    def format(self, record: logging.LogRecord) -> str:
        timestamp = format_apache_clf_timestamp(record.created)
        request: DefaultDict[str, str] = defaultdict(lambda: "-", **getattr(record, "request", {}))
        response: DefaultDict[str, str] = defaultdict(lambda: "-", **getattr(record, "response", {}))

        return (
            f"{request['remote_addr']} {request['user_id']} {request['username']} [{timestamp}]"
            f' "{self.request_format(request)}"'
            f" {response['status_code']} {response['content_length']}"
        )

    def request_format(self, request: DefaultDict[str, str]) -> str:
        return f"{request['method']} {request['path']} {request['protocol']}"


def format_apache_clf_timestamp(timestamp: int) -> str:
    """Convert a timestamp (unix time, integer seconds) to the datetime format for CLF"""

    monthname = [None, "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    when = dt.datetime.utcfromtimestamp(timestamp)

    s = "%02d/%3s/%04d %02d:%02d:%02d" % (
        when.day,
        monthname[when.month],
        when.year,
        when.hour,
        when.minute,
        when.second,
    )
    return s
