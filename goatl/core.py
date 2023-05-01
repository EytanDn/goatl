import logging
import inspect
import functools
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional, Union, TypeVar

_logger = logging.getLogger()
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
_logger.addHandler(handler)
_logger.setLevel(logging.DEBUG)

class BraceMessage(object):
    def __init__(self, fmt, *args, **kwargs):
        self.fmt = fmt
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        # warning maybe if not all args and kwargs are formatted? or missing?
        return self.fmt.format(*self.args, **self.kwargs)

DEFAULT_CALL_MESSAGE = "called {funcName} with {args} {kwargs}"
DEFAULT_RETURN_MESSAGE = "{funcName} returned {_return}"
DEFAULT_INIT_MESSAGE = "Initialized {className} with {args} {kwargs}"
DEFAULT_CALL_LEVEL = logging.INFO
DEFAULT_RETURN_LEVEL = logging.DEBUG
DEFAULT_INIT_LEVEL = logging.INFO

@dataclass
class Log:
    level: Optional[int] = None
    message: Optional[str] = None
    
    args: Optional[tuple] = field(default_factory=tuple)
    kwargs: Optional[dict] = field(default_factory=dict)
    
    logger: Optional[logging.Logger] = None
    
    def __post_init__(self):
        self.level = self.level or logging.INFO
        self.logger = self.logger or logging.getLogger()
    
    def __call__(self, *args, **kwargs) -> None:
        """log the message"""
        args = (*self.args, *args)
        kwargs = {**self.kwargs, **kwargs}
        self.logger.log(self.level, BraceMessage(self.message, *args, **kwargs))
        
    @staticmethod
    def _default_call_log(**kwargs) -> "Log":
        if not isinstance(kwargs.get("message", None), str):
            kwargs["message"] = DEFAULT_CALL_MESSAGE
        if kwargs.get("level", None) is None:
            kwargs["level"] = DEFAULT_CALL_LEVEL
        return Log(**kwargs)
    
    @staticmethod
    def _default_return_log(**kwargs) -> "Log":
        if not isinstance(kwargs.get("message", None), str):
            kwargs["message"] = DEFAULT_RETURN_MESSAGE
        if kwargs.get("level", None) is None:
            kwargs["level"] = DEFAULT_RETURN_LEVEL
        return Log(**kwargs)
    
    @staticmethod
    def _default_init_log(**kwargs) -> "Log":
        if not isinstance(kwargs.get("message", None), str):
            kwargs["message"] = DEFAULT_INIT_MESSAGE
        if kwargs.get("level", None) is None:
            kwargs["level"] = DEFAULT_INIT_LEVEL 
        return Log(**kwargs)

@dataclass
class CallLogParams:
    kwargs: Optional[dict] = field(default_factory=dict)

    def __post_init__(self): # TODO: seperate between level, call_level, reutrn_level
        self.call_log = Log._default_call_log(**self.kwargs)
        self.return_log = Log._default_return_log(**self.kwargs)

@dataclass
class ClassLogParams:
    kwargs: Optional[dict] = field(default_factory=dict)

    def __post_init__(self):
        self.method_log: Optional[CallLogParams] = CallLogParams(kwargs=self.kwargs)
        self.private_log: Optional[CallLogParams] = None
        self.property_log: Optional[CallLogParams] = None
        self.init_log: Optional[Log] = Log._default_init_log(**self.kwargs)

Loggable = TypeVar('Loggable', str, bool, int, float, list, dict, tuple, set, None)
Wrappable = TypeVar('Wrappable', Callable, type)

def _wrap_function(func: Callable,
                  params: CallLogParams) -> Callable:
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
            
            for name, value in inspect.getmembers(self): # TODO: what about static methods?
                if name.startswith("__"):
                    continue
                if name.startswith("_"):
                    if params.private_log:
                        _wrap_and_bind(value, _wrap_function, params.private_log)
                elif isinstance(value, property):
                    if params.property_log:
                        _wrap_and_bind(value.fget, _wrap_function, params.property_log)
                elif callable(value):
                    if params.method_log:
                        _wrap_and_bind(value, _wrap_function, params.method_log)
                        
            if params.init_log:
                params.init_log(className=wrapped.__name__, args=args, kwargs=kwargs)
    
    Wrapper.__name__ = wrapped.__name__
    Wrapper.__module__ = wrapped.__module__
    Wrapper.__qualname__ = wrapped.__qualname__
    Wrapper.__doc__ = wrapped.__doc__
    Wrapper.__annotations__ = wrapped.__annotations__
    
    return Wrapper

def _wrap_and_bind(func: Callable,
                  wrapper: Callable,
                  *args,
                  **kwargs) -> Callable:
    """Wraps a method and binds it to the instance"""
    func = getattr(func.__self__, func.__name__)
    instance = func.__self__
    wrapped = wrapper(getattr(instance.__class__, func.__name__), *args, **kwargs)
    bound_method = wrapped.__get__(instance, instance.__class__)
    setattr(instance, wrapped.__name__, bound_method)

    return getattr(instance, wrapped.__name__)

def _wrap(wrapped: Wrappable = None, **kwargs) -> Wrappable:
    """wrap a callable with a log"""
    if inspect.isclass(wrapped):
        class_log_params = ClassLogParams(kwargs)
        return _wrap_class(wrapped, class_log_params)
    else:
        call_log_params = CallLogParams(kwargs)
        return _wrap_function(wrapped, call_log_params)


def log(magic: Union[Wrappable, Loggable]=None, *args, 
        level: int=None,
        logger: logging.Logger=None,
        **kwargs) -> Union[Wrappable, None]:
    # """catch-all log method of goatl
    
    # ## mymodule.py:
    # >>> from goatl import log
    
    # ### function 
    # log can be used in a similar to the logging module
    
    # >>> log("hello world")
    # >>> # INFO:root:hello world
    
    # >>> log.debug("hello world")
    # >>> # DEBUG:root:hello world

    # ### method wrapper: 
    # it will log the function call and return value 
    # >>> @log
    # >>> def foo(x):
    # >>>     return x

    # >>> foo(21)
    # >>> # INFO:root:called foo with x=21
    # >>> # DEBUG:root:foo returned 21
    
    # ### class decorator: 
    # it will apply the log method to all methods of the class
    # __init__ which will be logged as an initialization
    # private methods (i.e methods starting with _) will not be logged by default
    # property getters and setters will not be logged by default # TODO:decide on this
    
    # >>> @log
    # >>> class Foo:
    # >>>     def __init__(self, x):
    # >>>         self.x = x
    
    # >>>     def bar(self):
    # >>>         return self.x * 2
    
    # >>> Foo(21).bar()
    # >>> # INFO:root:Initialized Foo <@objectid>  with x=21
    # >>> # INFO:root:called Foo.bar with self=<@objectid>
    # >>> # DEBUG:root:Foo.bar returned 42

    # ## Customization
    # method and class decoration is highly customizable
    # few examples of possible customizations:
    
    # ### Custom log level:
    # >>> @log(level="DEBUG", return_level="INFO")
    # >>> def foo(x):
    # >>>     return x * 2
    
    # >>> foo(21)
    # >>> # DEBUG:root:called foo with x=21
    # >>> # INFO:root:foo returned 42
    
    # ### Custom log message for class one class method:
    # >>> @log
    # >>> class Foo:
    # >>>     @log(message="[%(asctime)s] %(levelname)s: %(return)s from %(funcName)s")
    # >>>    def bar(self):
    # >>>         return 42
    
    # >>> Foo().bar()
    # >>> # [2021-01-01 00:00:00] INFO: 42 from Foo.bar

    # see the documentation for more details
    # Args:
    # """
    
    if isinstance(magic, Union[type, Callable, type(None)]):
        
        def decorate(wrapped: Wrappable) -> Wrappable:
            return _wrap(wrapped, level=level, logger=logger, **kwargs)
        
        if magic is None:
            return decorate
        return decorate(magic)
    else:
        Log(message=magic, level=level, logger=logger)(*args, **kwargs)

        
setattr(log, "info", functools.partial(log, level=logging.INFO))
setattr(log, "debug", functools.partial(log, level=logging.DEBUG))
setattr(log, "warning", functools.partial(log, level=logging.WARNING))
setattr(log, "warn", functools.partial(log, level=logging.WARN))
setattr(log, "error", functools.partial(log, level=logging.ERROR))
setattr(log, "critical", functools.partial(log, level=logging.CRITICAL))

