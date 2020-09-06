import logging

from conftest import LogWatcher

from flask_logging.filters import log_metadata
from flask_logging.filters import MetadataFilter


def test_metadata_filter(watchlog: LogWatcher) -> None:
    logger = logging.getLogger("test-logging-filter")
    logger.addFilter(MetadataFilter({"foo": "bar"}))

    logger.info("hello")

    record = watchlog.last("test-logging-filter")
    assert record.foo == "bar"  # type: ignore


def test_metadata_context(watchlog: LogWatcher) -> None:
    logger = logging.getLogger("test-logging-filter-context")

    logger.info("hello-1")
    with log_metadata({"foo": "baz"}, logger=logger):
        logger.info("hello-2")

    logger.info("hello-3")

    with log_metadata({"foo": "bat"}, logger="test-logging-filter-context"):
        logger.info("hello-4")

    missing = object()
    foos = [getattr(record, "foo", missing) for record in watchlog.filter("test-logging-filter-context")]
    assert foos == [missing, "baz", missing, "bat"]
