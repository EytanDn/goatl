import logging
from functools import wraps
from types import FunctionType
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
    LogParams,
    MethodLogParams,
)
from .defaults import DEFAULTS



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


def get_method_log_params(
    p: Optional[Union[MethodLogParams, bool, LogLevel]], none_is_true: bool = False
) -> Optional[MethodLogParams]:
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
