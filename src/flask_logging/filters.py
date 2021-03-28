import contextlib
import logging.config
from typing import Any
from typing import Dict
from typing import Iterator
from typing import Union

__all__ = ["MetadataFilter", "log_metadata"]


class MetadataFilter(logging.Filter):
    """
    A filter which imparts constant additional contextual information to log records as they are observed.

    Parameters
    ----------
    metadata: dict
        Dictionary of metadata to be added to all log records.

    """

    def __init__(self, metadata: Dict[str, Any]) -> None:
        self.metadata = metadata

    def filter(self, log_record: Any) -> bool:
        self._apply_metadata(log_record)
        return True

    def _apply_metadata(self, log_record: Any) -> None:
        log_record.__dict__.update(self.metadata)


@contextlib.contextmanager
def log_metadata(metadata: Dict[str, Any], logger: Union[None, str, logging.Filterer] = None) -> Iterator[None]:
    """
    Apply log metadata to all messages on the indicated handler or logger, for this context block

    Parameters
    ----------
    metadata: dict
        Dictionary of metadata to be added to all log records.
    logger: logger, handler, or logger name, optional.
        The logger to apply this filter to, defaults to the root logger.

    """

    if not isinstance(logger, logging.Filterer):
        logger = logging.getLogger(logger)

    metadata_filter = MetadataFilter(metadata)
    logger.addFilter(metadata_filter)

    yield

    logger.removeFilter(metadata_filter)
