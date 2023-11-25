import logging
from typing import (
    Callable,
    Union,
    Optional,
)
from typing_extensions import Unpack

from .data import (
    P,
    R,
    C,
    Logger,
    LogLevel,
    MethodLogParams,
    ClassLogParams,
)
from .helpers import (
    get_logger,
    wrap_function,
    wrap_class,
)

class log:
    @staticmethod
    def wrap(
        f: Optional[Callable[P, R]] = None,
        /,
        level: Optional[LogLevel] = None,
        logger: Optional[Logger] = None,
        **params: Unpack[MethodLogParams],
    ) -> Union[Callable[[Callable[P, R]], Callable[P, R]], Callable[P, R]]:
        def decorator(f: Callable[P, R]) -> Callable[P, R]:
            return wrap_function(f, logger, level, **params)

        if f is None:
            return decorator
        else:
            return decorator(f)
        
    @staticmethod
    def wrap_class(
        f: Optional[C] = None,
        /,
        level: Optional[LogLevel] = None,
        logger: Optional[Logger] = None,
        **params: Unpack[ClassLogParams],
    ) -> Union[C, Callable[[C], C]]:
        def decorator(cls: C) -> C:
            return wrap_class(cls, level, logger, **params)

        if f is None:
            return decorator
        else:
            return decorator(f)

    @staticmethod
    def log(
        level: LogLevel,
        m: Union[Optional[Callable[P, R]], str] = None,
        logger: Optional[Logger] = None,
        **params: Unpack[MethodLogParams],
    ) -> Union[Callable[[Callable[P, R]], Callable[P, R]], Callable[P, R], None]:
        """Log a message with a given level
        >>> log.log(logging.INFO, "Test message")
        """
        if isinstance(m, str):
            get_logger(logger).log(level, m)
            return None
        elif callable(m):
            return wrap_function(m, logger, level=level, **params)
        else:
            return log.wrap(None, logger=logger, level=level, **params)

    @staticmethod
    def info(
        f: Union[Optional[Callable[P, R]], str] = None,
        logger: Optional[Logger] = None,
        **params: Unpack[MethodLogParams],
    ) -> Union[Callable[[Callable[P, R]], Callable[P, R]], Callable[P, R], None]:
        return log.log(logging.INFO, f, logger, **params)

    @staticmethod
    def debug(
        f: Union[Optional[Callable[P, R]], str] = None,
        logger: Optional[Logger] = None,
        **params: Unpack[MethodLogParams],
    ) -> Union[Callable[[Callable[P, R]], Callable[P, R]], Callable[P, R], None]:
        return log.log(logging.DEBUG, f, logger, **params)

    @staticmethod
    def warn(
        f: Union[Optional[Callable[P, R]], str] = None,
        logger: Optional[Logger] = None,
        **params: Unpack[MethodLogParams],
    ) -> Union[Callable[[Callable[P, R]], Callable[P, R]], Callable[P, R], None]:
        if isinstance(f, str):
            log.log(logging.WARN, f, logger)
            return None
        elif callable(f):
            return wrap_function(f, logger, level=logging.WARN, **params)
        else:
            return log.wrap(None, logger=logger, level=logging.WARN, **params)

    @staticmethod
    def error(
        f: Union[Optional[Callable[P, R]], str] = None,
        logger: Optional[Logger] = None,
        **params: Unpack[MethodLogParams],
    ) -> Union[Callable[[Callable[P, R]], Callable[P, R]], Callable[P, R], None]:
        if isinstance(f, str):
            return log.log(logging.ERROR, f, logger)
        elif callable(f):
            return wrap_function(f, logger, level=logging.ERROR, **params)
        else:
            return log.wrap(None, logger=logger, level=logging.ERROR, **params)

    @staticmethod
    def critical(
        f: Union[Optional[Callable[P, R]], str] = None,
        logger: Optional[Logger] = None,
        **params: Unpack[MethodLogParams],
    ) -> Union[Callable[[Callable[P, R]], Callable[P, R]], Callable[P, R], None]:
        if isinstance(f, str):
            return log.log(logging.CRITICAL, f, logger)
        elif callable(f):
            return wrap_function(f, logger, level=logging.CRITICAL, **params)
        else:
            return log.wrap(None, logger=logger, level=logging.CRITICAL, **params)

