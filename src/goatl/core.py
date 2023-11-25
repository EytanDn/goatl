import logging
from typing import (
    Callable,
    Union,
    Optional,
    overload,
)
from typing_extensions import Unpack

from .types import (
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
    @overload
    @staticmethod
    def wrap(f: Callable[P, R], /) -> Callable[P, R]:
        """Wrap a function with default logging parameters
        >>> @log.wrap
        ... def func(a: int, b: str) -> str:
        ...     return f"Function called with {a} and {b}"
        func(1, "a")

        """

    @overload
    @staticmethod
    def wrap(
        f: None = None,
        /,
        level: Optional[LogLevel] = None,
        logger: Optional[Logger] = None,
        **params: Unpack[MethodLogParams],
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Wrap a function with custom logging parameters
        >>> @log.wrap(level=logging.WARN, call_level=logging.DEBUG)
        ... def func(a: int, b: str) -> str:
        ...     return f"Function called with {a} and {b}"
        func(1, "a")
        """

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

    @overload
    @staticmethod
    def wrap_class(
        f: C,
        /,
        **params: Unpack[ClassLogParams],
    ) -> C:
        """Wrap a class with default logging parameters
        >>> @log.wrap_class
        ... class A:
        ...     def __init__(self, a: int, b: str) -> None:
        ...         pass
        ...     def method(self, a: int, b: str) -> str:
        ...         return f"Method called with {a} and {b}"
        ...     def _private_method(self, a: int, b: str) -> str:
        ...         return f"Private method called with {a} and {b}"
        A(1, "a")
        """

    @overload
    @staticmethod
    def wrap_class(
        f: None = None,
        /,
        level: Optional[LogLevel] = None,
        logger: Optional[Logger] = None,
        **params: Unpack[ClassLogParams],
    ) -> Callable[[C], C]:
        """Wrap a class with custom logging parameters
        >>> @log.wrap_class(log_init=False, log_method={"call_level":logging.DEBUG})
        ... class A:
        ...     def __init__(self, a: int, b: str) -> None:
        ...         pass
        ...     def method(self, a: int, b: str) -> str:
        ...         return f"Method called with {a} and {b}"
        ...     def _private_method(self, a: int, b: str) -> str:
        ...         return f"Private method called with {a} and {b}"
        A(1, "a")
        """

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
        >>> log.log("Message", logging.INFO)
        """
        if isinstance(m, str):
            get_logger(logger).log(level, m)
            return None
        elif callable(m):
            return wrap_function(m, logger, level=level, **params)
        else:
            return log.wrap(None, logger=logger, level=level, **params)

    @overload
    @staticmethod
    def info(f: str, /, logger: Optional[Logger] = None) -> None:
        """Log a message with the INFO level
        >>> log.info("Message")
        """

    @overload
    @staticmethod
    def info(f: Callable[P, R]) -> Callable[P, R]:
        """Wrap a function with INFO level logging
        >>> @log.info
        ... def func(a: int, b: str) -> str:
        ...     return f"Function called with {a} and {b}"
        func(1, "a")
        """

    @overload
    @staticmethod
    def info(
        f: None = None,
        /,
        logger: Optional[Logger] = None,
        **params: Unpack[MethodLogParams],
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Wrap a function with custom INFO level logging
        >>> @log.info(call_level=logging.DEBUG)
        ... def func(a: int, b: str) -> str:
        ...     return f"Function called with {a} and {b}"
        func(1, "a")
        """

    @staticmethod
    def info(
        f: Union[Optional[Callable[P, R]], str] = None,
        logger: Optional[Logger] = None,
        **params: Unpack[MethodLogParams],
    ) -> Union[Callable[[Callable[P, R]], Callable[P, R]], Callable[P, R], None]:
        return log.log(logging.INFO, f, logger, **params)

    @overload
    @staticmethod
    def debug(f: str, /, logger: Optional[Logger] = None) -> None:
        """Log a message with the DEBUG level
        >>> log.debug("Message")
        """

    @overload
    @staticmethod
    def debug(f: Callable[P, R]) -> Callable[P, R]:
        """Wrap a function with DEBUG level logging
        >>> @log.debug
        ... def func(a: int, b: str) -> str:
        ...     return f"Function called with {a} and {b}"
        func(1, "a")
        """

    @overload
    @staticmethod
    def debug(
        f: None = None,
        /,
        logger: Optional[Logger] = None,
        **params: Unpack[MethodLogParams],
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Wrap a function with custom DEBUG level logging
        >>> @log.debug(return_level=logging.INFO)
        ... def func(a: int, b: str) -> str:
        ...     return f"Function called with {a} and {b}"
        func(1, "a")
        """

    @staticmethod
    def debug(
        f: Union[Optional[Callable[P, R]], str] = None,
        logger: Optional[Logger] = None,
        **params: Unpack[MethodLogParams],
    ) -> Union[Callable[[Callable[P, R]], Callable[P, R]], Callable[P, R], None]:
        return log.log(logging.DEBUG, f, logger, **params)

    @overload
    @staticmethod
    def warn(f: str, /, logger: Optional[Logger] = None) -> None:
        """Log a message with the WARN level
        >>> log.warn("Message")
        """

    @overload
    @staticmethod
    def warn(f: Callable[P, R]) -> Callable[P, R]:
        """Wrap a function with WARN level logging
        >>> @log.warn
        ... def func(a: int, b: str) -> str:
        ...     return f"Function called with {a} and {b}"
        func(1, "a")
        """

    @overload
    @staticmethod
    def warn(
        f: None = None,
        /,
        logger: Optional[Logger] = None,
        **params: Unpack[MethodLogParams],
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Wrap a function with custom WARN level logging
        >>> @log.warn(return_level=logging.INFO)
        ... def func(a: int, b: str) -> str:
        ...     return f"Function called with {a} and {b}"
        func(1, "a")
        """

    @staticmethod
    def warn(
        f: Union[Optional[Callable[P, R]], str] = None,
        logger: Optional[Logger] = None,
        **params: Unpack[MethodLogParams],
    ) -> Union[Callable[[Callable[P, R]], Callable[P, R]], Callable[P, R], None]:
        if isinstance(f, str):
            return log.log(logging.WARN, f, logger)
        elif callable(f):
            return wrap_function(f, logger, level=logging.WARN, **params)
        else:
            return log.wrap(None, logger=logger, level=logging.WARN, **params)

    @overload
    @staticmethod
    def error(f: str, /, logger: Optional[Logger] = None) -> None:
        """Log a message with the ERROR level
        >>> log.error("Message")
        """

    @overload
    @staticmethod
    def error(f: Callable[P, R]) -> Callable[P, R]:
        """Wrap a function with ERROR level logging
        >>> @log.error
        ... def func(a: int, b: str) -> str:
        ...     return f"Function called with {a} and {b}"
        func(1, "a")
        """

    @overload
    @staticmethod
    def error(
        f: None = None,
        /,
        logger: Optional[Logger] = None,
        **params: Unpack[MethodLogParams],
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Wrap a function with custom ERROR level logging
        >>> @log.error(return_level=logging.INFO)
        ... def func(a: int, b: str) -> str:
        ...     return f"Function called with {a} and {b}"
        func(1, "a")
        """

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

    @overload
    @staticmethod
    def critical(f: str, /, logger: Optional[Logger] = None) -> None:
        """Log a message with the CRITICAL level
        >>> log.critical("Message")
        """

    @overload
    @staticmethod
    def critical(f: Callable[P, R]) -> Callable[P, R]:
        """Wrap a function with CRITICAL level logging
        >>> @log.critical
        ... def func(a: int, b: str) -> str:
        ...     return f"Function called with {a} and {b}"
        func(1, "a")
        """

    @overload
    @staticmethod
    def critical(
        f: None = None,
        /,
        logger: Optional[Logger] = None,
        **params: Unpack[MethodLogParams],
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Wrap a function with custom CRITICAL level logging
        >>> @log.critical(return_level=logging.INFO)
        ... def func(a: int, b: str) -> str:
        ...     return f"Function called with {a} and {b}"
        func(1, "a")
        """

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

