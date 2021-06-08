import json
import logging
import os
import random
import string

import pytest
from flask_logging.handlers.json import JSONFormatter
from flask_logging.handlers.json import makeLogRecordfromJson
from flask_logging.handlers.redis import RedisLogWatcher
from flask_logging.handlers.redis import RedisPublisher

redis = pytest.importorskip("redis")


@pytest.fixture(scope="module")
def url():
    url = os.environ.get("REDIS_URL", "redis://localhost:6379/1")
    yield url


@pytest.fixture
def channel():

    extra = "".join(random.choices(string.ascii_letters, k=5))

    yield f"test-redis-channel-{extra}"


def test_publish_to_redis(url, channel):

    client = redis.Redis.from_url(url)
    pubsub = client.pubsub()
    pubsub.subscribe(channel)

    logger = logging.getLogger("test-redis-publisher")
    logger.setLevel(logging.INFO)
    handler = RedisPublisher(url, channel)
    handler.setLevel(logging.INFO)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    for _ in range(10):
        logger.info("A test message we send")
        raw_message = pubsub.parse_response(block=False, timeout=1)
        print(raw_message)
        if raw_message is None:
            continue
        message = pubsub.handle_message(raw_message, ignore_subscribe_messages=True)
        if message is not None:
            break

    assert message is not None
    assert message["channel"].decode("utf-8") == channel
    data = json.loads(message["data"])
    assert data["message"] == "A test message we send"


def test_listen_from_redis(watchlog, url, record, channel):

    watcher = RedisLogWatcher(url, channel, makeLogRecordfromJson)

    handler = RedisPublisher(url, channel)
    handler.setLevel(logging.INFO)
    handler.setFormatter(JSONFormatter())

    for _ in range(10):
        handler.emit(record)
        raw_message = watcher.pubsub.parse_response(block=False, timeout=1)
        if raw_message is None:
            continue
        print(raw_message)
        watcher.pubsub.handle_message(raw_message, ignore_subscribe_messages=True)
        if watchlog.any(record.name):
            break

    actual = watchlog.last(record.name)

    assert actual.levelno == record.levelno
    assert actual.msg == record.msg
