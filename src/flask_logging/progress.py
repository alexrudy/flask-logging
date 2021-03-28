"""
Log iterator progress messages
"""
import dataclasses as dc
import logging
import time
from typing import Generic
from typing import Iterator
from typing import Optional
from typing import TypeVar
from typing import Union

__all__ = ["ProgressReporter"]

T = TypeVar("T")
LogLevel = Union[str, int]


@dc.dataclass
class ProgressReporter(Generic[T]):
    """
    Wraps an iterator which will report iteration progress to a logger.

    Parameters
    ----------
    iterator: iterator
        Target iterator, which will be consumed by this progress reporter.
    logger: logging.Logger compatible object
        Where to log progress messages
    total: int, optional
        Number of items in the iterator. If not provided, will call len(iterator)
        to find out. It is expected that unbounded iterators, or iterators which don't
        support len() are passed with a value for `total`.
    title: str, optional
        Message to include in logging messages, defaults to "items", but can be set to provide
        a more descriptive progress update.
    level: int or str, optional
        Logging level to use for progress messages
    progress_interval: float, optional
        How often (at best effort) to log iterator progress, in seconds. This wrapper does not use a thread, and so
        cannot pre-empt iteration. Default is 0.5 seconds.
    progress_every: int, optional
        How many elements to consume before logging progress. Setting a value here will log progress every N elements,
        irrespecitve of the time which has passed since the previous message. Defaults to `None` (i.e. relies on
        processing time above).
    progress_start: int, optional
        Minimum number of elements which triggers an initial log message. For short loops, printing both the start (0%)
        and end message can be unnecessary, so setting this parameter to `None`.

    """

    iterator: Iterator[T]
    logger: logging.Logger = dc.field(default_factory=logging.getLogger)
    total: int = -1
    title: str = "items"
    level: LogLevel = logging.INFO

    progress_interval: Optional[float] = 0.5
    progress_every: Optional[int] = None
    progress_start: Optional[int] = None

    def __post_init__(self) -> None:

        if self.total == -1:
            # Accept the type error here - this iterator wrapper isn't actually useful
            # if we can't know the total number of items we are iterating over.
            self.total = len(self.iterator)  # type: ignore

        self.total = max(self.total, 0)

    def __len__(self) -> int:
        return len(self.iterator)  # type: ignore

    @property
    def _loglevel(self) -> int:
        if isinstance(self.level, str):
            return getattr(logging, self.level.upper())
        return self.level

    def __iter__(self) -> Iterator[T]:

        message = start = time.monotonic()

        if self.progress_start is not None:
            if self.total and self.total >= self.progress_start:
                self.logger.log(self._loglevel, f"[  0%] Processed 0 of {self.total} {self.title}")

        for i, entity in enumerate(self.iterator, start=1):

            yield entity

            if (
                i
                and (self.progress_interval and (time.monotonic() - message) > self.progress_interval)
                or (self.progress_every and (i % self.progress_every == 0))
            ):
                message = time.monotonic()
                self.logger.log(
                    self._loglevel,
                    f"[{i/self.total: 4.0%}] Processed {i} of {self.total} {self.title}",
                    extra=dict(total=self.total, processed=i, duration=time.monotonic() - start),
                )

        duration = time.monotonic() - start
        self.logger.log(
            self._loglevel,
            f"[100%] Processed {self.total} of {self.total} {self.title} in {duration:.1f}s",
            extra=dict(total=self.total, duration=duration),
        )
