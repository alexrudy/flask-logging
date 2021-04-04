import logging
from typing import Any
from typing import Callable
from typing import Dict
from typing import Tuple
from typing import TYPE_CHECKING
from typing import Union
from urllib.parse import parse_qs
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import urlunparse

if TYPE_CHECKING:
    import redis

from .json import makeLogRecordfromJson

ClientArgs = Union["redis.Redis", "redis.ConnectionPool", Tuple[str, int], str]
Deserialize = Callable[[str], logging.LogRecord]

DESERIALIERS: Dict[str, Deserialize] = {"json": makeLogRecordfromJson}


def _handle_redis_client_args(args: ClientArgs) -> "redis.Redis":
    """Handle arguments that should produce a REDIS client."""
    import redis

    if isinstance(args, redis.Redis):
        client: "redis.Redis" = args
    elif isinstance(args, redis.ConnectionPool):
        client = redis.Redis(connection_pool=args, decode_responses=False)
    elif isinstance(args, tuple):
        host, port = args
        client = redis.Redis(host, port, decode_responses=False)
    elif isinstance(args, str):
        client = redis.Redis.from_url(args)
    else:
        raise TypeError(f"Can't handle client arguments: {args!r}")
    return client


class RedisPublisher(logging.Handler):
    """A Redis publisher, which takes formatted log messages and publishes them to Redis."""

    def __init__(self, address: ClientArgs, channel: str):
        super().__init__()
        self.client = _handle_redis_client_args(address)
        self.channel = channel

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a single record."""
        try:
            msg = self.format(record)
            self.client.publish(self.channel, msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException:
            self.handleError(record)


class RedisLogWatcher:
    """Watch a Redis channel for logging"""

    thread = None

    def __init__(
        self,
        address: ClientArgs,
        channel: str,
        deserialize: Deserialize,
    ) -> None:
        super().__init__()
        self.pubsub = _handle_redis_client_args(address).pubsub()
        self.subscribe(channel)
        self.deserialize = deserialize

    @classmethod
    def from_url(cls, url: str) -> "RedisLogWatcher":
        """Create the log watcher from a URL"""

        # Get the options out of the URL
        result = urlparse(url)
        options = parse_qs(result.query)
        channel = options.pop("channel", "")
        format = options.pop("format", "json")
        if isinstance(format, list):
            raise TypeError(f"Multiple formats provided in URL: {format!r}")

        deserialize = DESERIALIERS[format]

        # Rebuild the URL without the query string.
        args = list(result)
        if "db" in options:
            args[4] = urlencode(options)
        else:
            args[4] = ""
        url = urlunparse(args)

        # Set up the object.
        if isinstance(channel, list):
            channel, *rest = channel
            obj = cls(url, channel, deserialize)
            for channel in rest:
                obj.subscribe(channel)
        else:
            obj = cls(url, channel, deserialize)
        return obj

    def _redis_responder(self, msg):
        """Given a Redis message, create the logrecord and handle it."""
        record = self.deserialize(msg["data"])
        logging.getLogger(record.name).handle(record)

    def subscribe(self, name):
        """Subscribe to an addtional channel."""
        self.pubsub.subscribe(**{name: self._redis_responder})

    def start(self):
        """Start the log watcher."""
        self.thread = self.pubsub.run_in_thread(sleep_time=0.01)

    def stop(self):
        """Stop the log watcher"""
        if self.thread is not None:
            self.thread.stop()

    def __enter__(self) -> "RedisLogWatcher":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()
