import functools
import logging.config
import os
from pathlib import Path
from typing import Dict
from typing import Union

import yaml


__all__ = ["setup_null_handler", "configure_logging"]


def setup_null_handler(logger: str) -> None:
    """Add a null handler to a given logger"""
    log = logging.getLogger(logger)
    log.propagate = True
    log.addHandler(logging.NullHandler())


@functools.singledispatch
def configure_logging(cfg: Dict) -> None:
    """Configure logging via a configuration dictionary"""
    cfg.setdefault("disable_existing_loggers", False)
    logging.config.dictConfig(cfg)


@configure_logging.register(os.PathLike)
@configure_logging.register(str)
def _cl_filename(filename: "Union[os.PathLike, str]") -> None:
    """Configure logging via a configuration in a YAML file"""
    with Path(filename).open("r") as s:
        cfg = yaml.safe_load(s)

    configure_logging(cfg)
