import logging
from typing import Any, NamedTuple, Optional, Type, TypeVar, TypedDict, Union
from typing_extensions import ParamSpec

P = ParamSpec('P')
R = TypeVar('R')
C = TypeVar('C', bound=Type[Any])
Logger = Union[logging.Logger, str]
LogLevel = int

class LogParams(NamedTuple):
    msg: str
    level: LogLevel
    logger: Optional[Logger]

class MethodLogParams(TypedDict, total=False):
    call_msg: Optional[str]
    call_level: Optional[LogLevel]
    return_msg: Optional[str]
    return_level: Optional[LogLevel]

class ClassLogParams(TypedDict, total=False):
    log_init: Optional[Union[LogParams, bool]]
    log_methods: Optional[Union[MethodLogParams, bool, LogLevel]]
    log_prvt_mthd: Optional[Union[MethodLogParams, bool, LogLevel]]

