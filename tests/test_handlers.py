import logging

import pytest
from flask_logging import ClickStyleFormatter
from flask_logging import LogLevelDict


def test_loglevel_dict() -> None:

    lld: LogLevelDict[int] = LogLevelDict()
    assert not lld
    assert len(lld) == 0

    assert repr(lld).startswith("LogLevelDict")

    lld["INFO"] = 10

    assert lld["INFO"] == 10
    assert lld["DEBUG"] == 10
    assert list(lld) == [logging.INFO]

    assert "INFO" in lld
    assert "DEBUG" in lld
    assert "WARNING" not in lld

    lld["DEBUG"] = 5
    lld["WARNING"] = 8

    del lld["INFO"]
    assert "INFO" in lld
    assert lld["INFO"] == 8

    lld["DEBUG"] = 6
    assert lld["debug"] == 6
    with pytest.raises(KeyError):
        del lld["INFO"]


def test_formatter(record: logging.LogRecord) -> None:
    fmt = ClickStyleFormatter("[%(clevelname)s] %(msg)s")

    msg = fmt.format(record)

    # TODO Properly test that this message contains ANSI escape codes
    assert msg != f"[{logging.getLevelName(record.levelno)}] Some message here!"
