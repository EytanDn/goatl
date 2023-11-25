import logging
from typing import (
    TypeVar,
    Union,
    Optional,
    TypedDict,
    NamedTuple,
    Type,
    Any
)
from typing_extensions import ParamSpec

P = ParamSpec("P")
R = TypeVar("R")
C = TypeVar("C", bound=Type[Any])


Logger = Union[logging.Logger, str]
"a logger object or a logger name"
LogLevel = int
"logging.(DEBUG|INFO|WARN|ERROR|CRITICAL)"


class LogParams(NamedTuple):
    """Parameters for logging"""
    msg: str
    level: LogLevel
    logger: Optional[Logger] = None


class MethodLogParams(TypedDict, total=False):
    """Parameters for logging a method call and return"""
    call_msg: Optional[str]
    call_level: Optional[LogLevel]
    return_msg: Optional[str]
    return_level: Optional[LogLevel]

class ClassLogParams(TypedDict, total=False):
    """Parameter specification for logging a class"""
    log_init: Optional[Union[LogParams, bool]]
    log_methods: Optional[Union[MethodLogParams, bool, LogLevel]]
    log_prvt_mthd: Optional[Union[MethodLogParams, bool, LogLevel]]

    
__all__ = [
    "P",
    "R",
    "Logger",
    "LogLevel",
    "LogParams",
    "MethodLogParams",
    "ClassLogParams",
    "DEFAULTS",
]
