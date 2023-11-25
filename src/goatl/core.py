import logging
from functools import wraps
from types import FunctionType
from typing import (
    Any,
    Callable,
    Type,
    TypeVar,
    Union,
    Optional,
    overload,
    TypedDict,
    NamedTuple,
)
from typing_extensions import ParamSpec, Unpack, Annotated

P = ParamSpec("P")
R = TypeVar("R")

Logger = Union[logging.Logger, str]
LogLevel = Annotated[
    int,
    "logging.DEBUG | logging.INFO | logging.WARN | logging.ERROR | logging.CRITICAL",
]


class LogParams(NamedTuple):
    msg: str
    level: LogLevel
    logger: Optional[Logger] = None


class MethodLogParams(TypedDict, total=False):
    call_msg: Optional[str]
    call_level: Optional[LogLevel]
    return_msg: Optional[str]
    return_level: Optional[LogLevel]


class ClassLogParams(TypedDict, total=False):
    log_init: Optional[Union[LogParams, bool]]
    log_methods: Optional[Union[MethodLogParams, bool, LogLevel]]
    log_prvt_mthd: Optional[Union[MethodLogParams, bool, LogLevel]]


class DEFAULTS:
    CALL_MSG = "Calling {funcName} with {args} and {kwargs}"
    RETURN_MSG = "Returned {result}"
    CALL_LEVEL = logging.INFO
    RETURN_LEVEL = logging.DEBUG
    INIT_MSG = "Initialized {args[0]}"
    INIT_LEVEL = logging.DEBUG


def get_logger(logger: Optional[Logger]) -> logging.Logger:
    if isinstance(logger, logging.Logger):
        pass
    elif isinstance(logger, str):
        logger = logging.getLogger(logger)
    else:
        logger = logging.getLogger(__name__)

    return logger


def wrap_function(
    f: Callable[P, R],
    logger: Optional[Logger] = None,
    level: Optional[LogLevel] = None,
    **params: Unpack[MethodLogParams],
) -> Callable[P, R]:
    if getattr(f, "__log_wrapped__", False):
        return f
    
    funcName = f.__name__

    call_msg = params.get("call_msg", DEFAULTS.CALL_MSG)
    call_level = params.get("call_level", level or DEFAULTS.CALL_LEVEL)
    return_msg = params.get("return_msg", DEFAULTS.RETURN_MSG)
    return_level = params.get("return_level", level or DEFAULTS.RETURN_LEVEL)

    @wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if call_msg is not None and call_level is not None:
            get_logger(logger).log(
                call_level, call_msg.format(funcName=funcName, args=args, kwargs=kwargs)
            )

        result = f(*args, **kwargs)

        if return_msg is not None and return_level is not None:
            get_logger(logger).log(
                return_level, return_msg.format(funcName=funcName, result=result)
            )

        return result

    setattr(wrapper, "__log_wrapped__", True)
    
    return wrapper


C = TypeVar("C", bound=Type[Any])

def get_method_log_params(p: Optional[Union[MethodLogParams, bool, LogLevel]], none_is_true: bool = False) -> Optional[MethodLogParams]:
    if p is None:
        if none_is_true:
            return MethodLogParams()
        else:
            return None
    elif p is True:
        return MethodLogParams()
    elif isinstance(p, int):
        return MethodLogParams(call_level=p, return_level=p)
    else:
        return p


def wrap_class(
    cls: C,
    /,
    level: Optional[LogLevel] = None,
    logger: Optional[Logger] = None,
    log_init: Optional[Union[LogParams, bool, LogLevel]] = None,
    log_methods: Optional[Union[MethodLogParams, bool, LogLevel]] = None,
    log_prvt_mthd: Optional[Union[MethodLogParams, bool, LogLevel]] = None,
) -> C:
    log_methods = get_method_log_params(log_methods, none_is_true=True)
    log_prvt_mthd = get_method_log_params(log_prvt_mthd)
    for name, value in cls.__dict__.items():
        if log_methods and isinstance(value, classmethod):
            setattr(
                cls,
                name,
                classmethod(
                    wrap_function(
                        value.__func__, level=level, logger=logger, **log_methods
                    )
                ),
            )
        elif log_methods and isinstance(value, staticmethod):
            setattr(
                cls,
                name,
                staticmethod(
                    wrap_function(
                        value.__func__, level=level, logger=logger, **log_methods
                    )
                ),
            )

        if not isinstance(value, FunctionType):
            continue

        if name == "__init__":
            if log_init is False:
                continue
            elif log_init is None or log_init is True:
                log_init = LogParams(DEFAULTS.INIT_MSG, DEFAULTS.INIT_LEVEL)
            elif isinstance(log_init, LogLevel):
                log_init = LogParams(DEFAULTS.INIT_MSG, log_init)

            setattr(
                cls,
                name,
                wrap_function(
                    value,
                    level=log_init.level or level,
                    call_msg=log_init.msg,
                    logger=logger,
                    return_msg=None,
                ),
            )
            continue
        elif log_prvt_mthd and name.startswith("_"):
            setattr(
                cls,
                name,
                wrap_function(
                    value,
                    logger=logger,
                    level=level,
                    **log_prvt_mthd,
                ),
            )
            continue
        elif log_methods is None:
            continue
        
        setattr(
            cls,
            name,
            wrap_function(value, level=level, logger=logger, **log_methods),
        )

    return cls


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


@log.wrap_class(log_init=False, log_methods=False)
class A:
    def __init__(self, a: int, b: str) -> None:
        pass

    def method(self, a: int, b: str) -> str:
        return f"Method called with {a} and {b}"

    def method2(self, a: int, b: str) -> str:
        return f"Method called with {a} and {b}"

    def method3(self, a: int, b: str) -> str:
        return f"Method called with {a} and {b}"


if __name__ == "__main__":
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s - %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    a = A(1, "a")
    a.method(1, "a")
    a.method2(1, "a")
