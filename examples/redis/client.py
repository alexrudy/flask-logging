#!/usr/bin/env python3
import logging
import sys
import time

from flask_logging.handlers.click import ComposeClickFormatter
from flask_logging.handlers.redis import RedisLogWatcher


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

    watcher = RedisLogWatcher.from_url(url)
    watcher.subscribe("example-application")

    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(ComposeClickFormatter())

    logger.addHandler(handler)
    logger.setLevel(logging.NOTSET)

    with watcher:
        time.sleep(20)

    return 0


if __name__ == "__main__":
    sys.exit(main())
