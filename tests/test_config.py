import logging
from pathlib import Path
from typing import Any
from typing import Union

import pytest
import yaml

from flask_logging.config import configure_logging
from flask_logging.config import setup_null_handler


FixtureRequest = Any


@pytest.fixture(params=["yaml", "dict"])
def mode(request: FixtureRequest) -> str:
    return request.param


@pytest.fixture(params=list((Path(__file__).parent / "configurations").glob("*.yml")))
def configuration(request: FixtureRequest, mode: str) -> Union[str, Path]:
    if mode == "yaml":
        return request.param
    elif mode == "dict":
        with request.param.open("r") as stream:
            return yaml.safe_load(stream)
    else:
        raise ValueError(mode)  # pragma: nocover


def test_configure(configuration: Union[str, Path]) -> None:
    """Smoke-test configuration using the documented configurations"""
    configure_logging(configuration)
    logger = logging.getLogger("foo.bar.baz")
    assert len(logger.handlers) == 2


def test_null_hanlder() -> None:
    logger = logging.getLogger("foo.bar.bat")
    setup_null_handler("foo.bar.bat")
    assert len(logger.handlers) == 1
