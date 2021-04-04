#!/usr/bin/env python3
import datetime as dt
import logging
import sys
import time

from flask_logging.handlers.json import JSONFormatter
from flask_logging.handlers.redis import RedisPublisher


class FakeComposeFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.compose = {  # type: ignore
            "project": "example-flask-project",
            "service": "logging-test-service",
            "container-number": "2",
        }

        return True


def main() -> int:

    url = sys.argv[1]

    logger = logging.getLogger()
    logger.addFilter(FakeComposeFilter())
    redis_handler = RedisPublisher(url, "example-application")
    redis_handler.setFormatter(JSONFormatter())
    logger.addHandler(redis_handler)
    logger.setLevel(logging.NOTSET)

    try:
        while True:
            now = dt.datetime.now()
            message = f"The time now is {now:%H:%M:%S}"
            if now.second % 15 == 0:
                level = logging.ERROR
            elif now.second % 3 == 0:
                level = logging.WARNING
            elif now.second % 5 == 0:
                level = logging.INFO
            else:
                level = logging.DEBUG
            logger.log(level, message)
            time.sleep(0.5)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
