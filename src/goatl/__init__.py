# type: ignore[attr-defined]
"""Greatest of all time logger"""

import sys
from .core import log
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL, WARN


if sys.version_info >= (3, 8):
    from importlib import metadata as importlib_metadata
else:
    import importlib_metadata


def get_version() -> str:
    try:
        return importlib_metadata.version(__name__)
    except importlib_metadata.PackageNotFoundError:  # pragma: no cover
        return "unknown"


version: str = get_version()

__all__ = ["log", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "WARN"]

log.info