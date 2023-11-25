from .data import (
    P,
    R,
    C,
    Logger,
    LogLevel,
    MethodLogParams,
    ClassLogParams,
)

from typing import Callable, Optional, Union, overload
from typing_extensions import Unpack

class log:
    @overload
    @staticmethod
    def wrap(f: Callable[P, R],/) -> Callable[P, R]:
        """Wrap a function with default logging parameters
        >>> @log.wrap
        ... def func(a: int, b: str) -> str:
        ...     return f"Function called with {a} and {b}"
        func(1, "a")

        """
    @overload
    @staticmethod
    def wrap(f: None = ..., level: Optional[LogLevel] = ..., logger: Optional[Logger] = ..., **params: Unpack[MethodLogParams]) -> Callable[[Callable[P, R]], Callable[P, R]]: 
        """Wrap a function with custom logging parameters
        >>> @log.wrap(level=logging.WARN, call_level=logging.DEBUG)
        ... def func(a: int, b: str) -> str:
        ...     return f"Function called with {a} and {b}"
        func(1, "a")
        """
    @overload
    @staticmethod
    def wrap_class(f: C, **params: Unpack[ClassLogParams]) -> C: 
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
    @overload
    @staticmethod
    def wrap_class(f: None = ..., level: Optional[LogLevel] = ..., logger: Optional[Logger] = ..., **params: Unpack[ClassLogParams]) -> Callable[[C], C]:
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
    @staticmethod
    def log(level: LogLevel, m: Union[Optional[Callable[P, R]], str] = ..., logger: Optional[Logger] = ..., **params: Unpack[MethodLogParams]) -> Union[Callable[[Callable[P, R]], Callable[P, R]], Callable[P, R], None]: ...
    @overload
    @staticmethod
    def info(f: str, logger: Optional[Logger] = ...) -> None:
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
    def info(f: None = ..., logger: Optional[Logger] = ..., **params: Unpack[MethodLogParams]) -> Callable[[Callable[P, R]], Callable[P, R]]: 
        """Wrap a function with custom INFO level logging
        >>> @log.info(call_level=logging.DEBUG)
        ... def func(a: int, b: str) -> str:
        ...     return f"Function called with {a} and {b}"
        func(1, "a")
        """
    @overload
    @staticmethod
    def debug(f: str, logger: Optional[Logger] = ...) -> None: 
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
    def debug(f: None = ..., logger: Optional[Logger] = ..., **params: Unpack[MethodLogParams]) -> Callable[[Callable[P, R]], Callable[P, R]]: 
        """Wrap a function with custom DEBUG level logging
        >>> @log.debug(return_level=logging.INFO)
        ... def func(a: int, b: str) -> str:
        ...     return f"Function called with {a} and {b}"
        func(1, "a")
        """
    @overload
    @staticmethod
    def warn(f: str, logger: Optional[Logger] = ...) -> None: 
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
    def warn(f: None = ..., logger: Optional[Logger] = ..., **params: Unpack[MethodLogParams]) -> Callable[[Callable[P, R]], Callable[P, R]]: 
        """Wrap a function with custom WARN level logging
        >>> @log.warn(return_level=logging.INFO)
        ... def func(a: int, b: str) -> str:
        ...     return f"Function called with {a} and {b}"
        func(1, "a")
        """
    @overload
    @staticmethod
    def error(f: str, logger: Optional[Logger] = ...) -> None: 
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
    def error(f: None = ..., logger: Optional[Logger] = ..., **params: Unpack[MethodLogParams]) -> Callable[[Callable[P, R]], Callable[P, R]]: 
        """Wrap a function with custom ERROR level logging
        >>> @log.error(return_level=logging.INFO)
        ... def func(a: int, b: str) -> str:
        ...     return f"Function called with {a} and {b}"
        func(1, "a")
        """
    @overload
    @staticmethod
    def critical(f: str, logger: Optional[Logger] = ...) -> None: 
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
    def critical(f: None = ..., logger: Optional[Logger] = ..., **params: Unpack[MethodLogParams]) -> Callable[[Callable[P, R]], Callable[P, R]]: 
        """Wrap a function with custom CRITICAL level logging
        >>> @log.critical(return_level=logging.INFO)
        ... def func(a: int, b: str) -> str:
        ...     return f"Function called with {a} and {b}"
        func(1, "a")
        """
