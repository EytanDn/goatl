import sys
import os
import logging
import inspect
import functools
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union, TypeVar, Tuple, Dict
from .utils import _wrap_and_bind, _transfer_class_meta


Reprable = TypeVar("Reprable", Callable, type)
Wrappable = Union[Callable, type(None)]


class BraceMessage(object):
    def __init__(self, fmt: str, *args, **kwargs):
        self.fmt: str = fmt
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        # TODO: warning maybe if not all args and kwargs are formatted? or missing?
        return self.fmt.format(*self.args, **self.kwargs)


DEFAULT_CALL_MESSAGE = "called {funcName} with {args} {kwargs}"
DEFAULT_RETURN_MESSAGE = "{funcName} returned {_return}"
DEFAULT_INIT_MESSAGE = "Initialized {className} with {args} {kwargs}"
DEFAULT_CALL_LEVEL = logging.INFO
DEFAULT_RETURN_LEVEL = logging.DEBUG
DEFAULT_INIT_LEVEL = logging.INFO


@dataclass(slots=True)
class _Log:
    level: Optional[int] = None
    message: Optional[str] = None

    args: Optional[Tuple] = field(default_factory=tuple)
    kwargs: Optional[Dict] = field(default_factory=dict)

    logger: Optional[logging.Logger] = None

    def __post_init__(self):
        if isinstance(self.level, str):
            self.level = getattr(logging, self.level.upper())
        elif self.level in log.levels:
            self.level = log.levels[self.level]

        if self.level is None:
            # _logger.warning(f"level is None, using default level {DEFAULT_CALL_LEVEL}")
            self.level = DEFAULT_CALL_LEVEL

        self.message = self.message or DEFAULT_CALL_MESSAGE
        self.logger = self.logger or logging.getLogger()

    def __call__(self, *args, **kwargs) -> None:
        """log the message"""
        args = (*self.args, *args)
        kwargs = {**self.kwargs, **kwargs}
        self.logger.log(self.level, BraceMessage(self.message, *args, **kwargs))

    @staticmethod
    def _from_kwargs(
        kwargs: Dict, default_message: str, default_level: int, prefix: str
    ) -> "_Log | None":
        message = kwargs.get(f"{prefix}_message", None)
        level = kwargs.get(f"{prefix}_level", None)

        if not isinstance(message, str):
            message = kwargs.get("message", None)

        if level is None:
            level = kwargs.get("level", None)

        if not isinstance(message, str):
            message = default_message

        if level is None:
            level = default_level

        if message is None and level is None:
            return None

        return _Log(message=message, level=level, logger=kwargs.get("logger", None))


@dataclass
class CallLogParams:
    kwargs: Optional[Dict] = field(default_factory=dict)

    def __post_init__(self):  # TODO: seperate between level, call_level, reutrn_level
        # if call_message is present use it,
        # else use message if present, else use default
        # if call_level is present use it, else use level if present, else use default

        self.call_log = _Log._from_kwargs(
            self.kwargs, DEFAULT_CALL_MESSAGE, DEFAULT_CALL_LEVEL, prefix="call"
        )
        self.return_log = _Log._from_kwargs(
            self.kwargs, DEFAULT_RETURN_MESSAGE, DEFAULT_RETURN_LEVEL, prefix="return"
        )


@dataclass
class ClassLogParams:
    kwargs: Optional[Dict] = field(default_factory=dict)

    def __post_init__(self):
        self.method_log: Optional[CallLogParams] = CallLogParams(kwargs=self.kwargs)
        self.private_log: Optional[CallLogParams] = None
        self.property_log: Optional[CallLogParams] = None
        self.init_log: Optional[_Log] = _Log._from_kwargs(
            self.kwargs, DEFAULT_INIT_MESSAGE, DEFAULT_INIT_LEVEL, prefix="init"
        )

        if any(
            [
                key.startswith("private")
                for key, value in self.kwargs.items()
                if value is not None
            ]
        ):
            p_kwargs = {
                "message": self.kwargs.get("private_message", None),
                "level": self.kwargs.get("private_level", None),
            }
            self.private_log = CallLogParams(kwargs={**self.kwargs, **p_kwargs})


def _wrap_function(func: Callable, params: CallLogParams) -> Callable:
    """wrap a function with a log"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if params.call_log:
            params.call_log(funcName=func.__name__, args=args, kwargs=kwargs)

        return_value = func(*args, **kwargs)

        if params.return_log:
            params.return_log(funcName=func.__name__, _return=return_value)

        return return_value

    setattr(wrapper, "__log_params__", params)

    return wrapper


def _wrap_class(wrapped: type, params: ClassLogParams) -> type:
    """wrap a class with a log"""

    class Wrapper(wrapped):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            for name, value in inspect.getmembers(self):
                if name.startswith("__"):
                    continue
                if name.startswith("_"):
                    if params.private_log:
                        _wrap_and_bind(value, _wrap_function, params.private_log)
                elif isinstance(value, property):
                    if params.property_log:
                        _wrap_and_bind(value.fget, _wrap_function, params.property_log)
                elif inspect.ismethod(value) or inspect.isfunction(value):
                    if params.method_log:
                        _wrap_and_bind(value, _wrap_function, params.method_log)
                elif inspect.isclass(value):
                    setattr(self, name, _wrap_class(value, params))

            if params.init_log:
                params.init_log(className=wrapped.__name__, args=args, kwargs=kwargs)

    return _transfer_class_meta(wrapped, Wrapper)


def _wrap(wrapped: Wrappable = None, **kwargs) -> Wrappable:
    """wrap a callable with a log"""
    if inspect.isclass(wrapped):
        class_log_params = ClassLogParams(kwargs)
        return _wrap_class(wrapped, class_log_params)

    call_log_params = CallLogParams(kwargs)
    return _wrap_function(wrapped, call_log_params)


class log:
    def __init__(
        self,
        magic: Union[Wrappable, Reprable] = None,
        /,
        *args: Optional[Tuple[Any]],
        message: Optional[str] = None,
        level: Optional[int] = None,
        logger: Optional[logging.Logger] = None,
        call_message: Optional[str] = None,
        call_level: Optional[int] = None,
        return_message: Optional[str] = None,
        return_level: Optional[int] = None,
        init_message: Optional[str] = None,
        init_level: Optional[int] = None,
        private_message: Optional[str] = None,
        private_level: Optional[int] = None,
        property_message: Optional[str] = None,
        property_level: Optional[int] = None,
        **kwargs,
    ) -> Union[Wrappable, None]:
        self._f = None

        if logger is not None:
            if isinstance(logger, str):
                logger = logging.getLogger(logger)
            else:
                assert isinstance(
                    logger, logging.Logger
                ), "logger must be a string or a logger"

        if isinstance(magic, Callable) or isinstance(magic, type(None)):
            log_kwargs = dict(
                message=message,
                level=level,
                call_message=call_message,
                call_level=call_level,
                return_message=return_message,
                return_level=return_level,
                init_message=init_message,
                init_level=init_level,
                private_message=private_message,
                private_level=private_level,
                property_message=property_message,
                property_level=property_level,
                logger=logger,
            )

            def decorate(wrapped: Wrappable) -> Wrappable:
                self._f = _wrap(wrapped, **log_kwargs, **kwargs)

            if magic is None:
                self._f = decorate
            self._f = decorate(magic)
        else:
            if level is None:  # TODO: maybe search for level in current score?
                level = logging.INFO

            _Log(message=magic, level=level, logger=logger)(*args, **kwargs)

    def __call__(self, *args, **kwargs) -> Union[Wrappable, None]:
        if self._f is not None:
            return self._f(*args, **kwargs)

    @staticmethod
    def info(
        magic: Union[Wrappable, Reprable] = None,
        /,
        *args: Optional[Tuple[Any]],
        message: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ) -> Union[Wrappable, None]:
        """shortcut to log at info level"""
        return log(
            magic, *args, message=message, level=logging.INFO, logger=logger, **kwargs
        )

    @staticmethod
    def debug(
        magic: Union[Wrappable, Reprable] = None,
        /,
        *args: Optional[Tuple[Any]],
        message: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ) -> Union[Wrappable, None]:
        """shortcut to log at debug level"""
        return log(
            magic, *args, message=message, level=logging.DEBUG, logger=logger, **kwargs
        )

    @staticmethod
    def warning(
        magic: Union[Wrappable, Reprable] = None,
        /,
        *args: Optional[Tuple[Any]],
        message: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ) -> Union[Wrappable, None]:
        """shortcut to log at warning level"""
        return log(
            magic,
            *args,
            message=message,
            level=logging.WARNING,
            logger=logger,
            **kwargs,
        )

    @staticmethod
    def error(
        magic: Union[Wrappable, Reprable] = None,
        /,
        *args: Optional[Tuple[Any]],
        message: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ) -> Union[Wrappable, None]:
        """shortcut to log at error level"""
        return log(
            magic, *args, message=message, level=logging.ERROR, logger=logger, **kwargs
        )

    @staticmethod
    def critical(
        magic: Union[Wrappable, Reprable] = None,
        /,
        *args: Optional[Tuple[Any]],
        message: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ) -> Union[Wrappable, None]:
        """shortcut to log at critical level"""
        return log(
            magic,
            *args,
            message=message,
            level=logging.CRITICAL,
            logger=logger,
            **kwargs,
        )

    @staticmethod
    def getLogger(name: Optional[str] = None) -> logging.Logger:
        """shortcut to get a logger"""
        return logging.getLogger(name)

    @staticmethod
    def basicConfig(**kwargs):
        """shortcut to basicConfig"""
        return logging.basicConfig(**kwargs)

    @staticmethod
    def Formatter(fmt: str) -> logging.Formatter:
        """shortcut to Formatter"""
        return logging.Formatter(fmt)

    @staticmethod
    def FileHandler(filename: str) -> logging.FileHandler:
        """shortcut to FileHandler"""
        return logging.FileHandler(filename)

    @staticmethod
    def StreamHandler(stream: Any) -> logging.StreamHandler:
        """shortcut to StreamHandler"""
        return logging.StreamHandler(stream)

    levels = {
        info: logging.INFO,
        debug: logging.DEBUG,
        warning: logging.WARNING,
        error: logging.ERROR,
        critical: logging.CRITICAL,
    }

    @staticmethod
    def addStdoutHandler(
        fmt: Union[logging.Formatter, str] = None,
        logger: Optional[logging.Logger] = None,
        level: Optional[int] = logging.INFO,
    ):
        """shortcut to add a stdout handler to the root logger"""
        if logger is not None:
            assert isinstance(logger, logging.Logger), "logger must be a logging.Logger"
        assert (
            isinstance(level, int) or level in log.levels
        ), "level must be an int or a log.level"
        if fmt is not None:
            assert isinstance(
                fmt, (logging.Formatter, str)
            ), "fmt must be a logging.Formatter or a string"

        handler = logging.StreamHandler(stream=sys.stdout)
        if logger is None:
            logger = logging.getLogger()

        if isinstance(fmt, str):
            handler.setFormatter(logging.Formatter(fmt))
        elif isinstance(fmt, logging.Formatter):
            handler.setFormatter(fmt)

        logger.addHandler(handler)
        logger.setLevel(log.levels.get(level, level))


# def _add_file_handler(filename: Optional[str]=None,
#                       fmt: Union[logging.Formatter, str]=None,
#                       logger: Optional[logging.Logger]=None,
#                       level: Optional[int]=logging.DEBUG):
#     """shortcut to add a file handler to the root logger
#     if filename is not provided, it will be set to the name of the current script
#     with a .log extension
#     """
#     if filename is not None:
#         assert isinstance(filename, str), \
#                 "filename must be a string"
#     if logger is not None:
#         assert isinstance(logger, logging.Logger), \
#                 "logger must be a logging.Logger"
#     assert isinstance(level, int) or level in levels, \
#                 "level must be an int or a log.level"
#     if fmt is not None:
#         assert isinstance(fmt,(logging.Formatter, str)), \
#                 "fmt must be a logging.Formatter or a string"

#     filename = filename or os.path.splitext(os.path.basename(sys.argv[0]))[0]
#     filename = filename.replace(" ", "_") + ".log"
#     handler = logging.FileHandler(filename=filename)
#     if isinstance(fmt, str):
#         handler.setFormatter(logging.Formatter(fmt))
#     elif isinstance(fmt, logging.Formatter):
#         handler.setFormatter(fmt)

#     if logger is None:
#         logger = logging.getLogger()
#     logger.addHandler(handler)
#     logger.setLevel(levels.get(level, level))

# setattr(log, "addFileHandler", _add_file_handler)
