import logging
import inspect
import functools
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional, Union, TypeVar

_logger = logging.getLogger()
_logger.addHandler(logging.StreamHandler(stream=sys.stdout))
_logger.setLevel(logging.DEBUG)

class BraceMessage(object):
    def __init__(self, fmt, *args, **kwargs):
        self.fmt = fmt
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        # warning if not all args and kwargs are formatted? or missing?
        return self.fmt.format(*self.args, **self.kwargs)

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
    def _default_call_log() -> "Log":
        return Log(message="called {funcName} with {args} {kwargs}")
    
    @staticmethod
    def _default_return_log() -> "Log":
        return Log(message="{funcName} returned {_return}")
    
    @staticmethod
    def _default_init_log() -> "Log":
        return Log(message="Initialized {class} with {args} {kwargs}")

@dataclass
class CallLogParams:
    call_log: Optional[Log] = field(
        default_factory=Log._default_call_log
    )
    return_log: Optional[Log] = field(
        default_factory=Log._default_return_log
    )

@dataclass
class ClassLogParams:
    call_log: Optional[CallLogParams] = field(
        default_factory=CallLogParams
    )
    init_log: Optional[Log] = field(
        default_factory=Log._default_init_log
    )
    private_log: Optional[Log] = None
    property_log: Optional[Log] = None


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
            if params.init_log:
                params.init_log(wrapped.__name__, kwargs)
                
            super().__init__(*args, **kwargs)
            
        def __getattribute__(self, name):
            member = super().__getattribute__(name)
            
            if isinstance(member, property) and params.property_log:
                return _wrap_function(member, params.property_log)
            
            if name.startswith("_"):
                if getattr(member, "__log_params__", None):
                    return member
                if params.private_log:
                    return _wrap_function(member, params.private_log)
                return member
            
            if inspect.ismethod(member):
                if getattr(member, "__log_params__", None):
                    return member
                return _wrap_function(member, params.call_log)
            
            return member
        
    return Wrapper
    

def _wrap(outer_wrapped: Wrappable = None, *args, **kwargs) -> Wrappable:
    """wrap a callable with a log"""
    
    print(outer_wrapped, args, kwargs)
    
    def decorate(wrapped: Wrappable) -> Wrappable:
        print("Decorating")
        if inspect.isclass(wrapped):
            print("wrapping class")
            class_log_params = ClassLogParams(*args, **kwargs)
            return _wrap_class(wrapped, class_log_params)
        else:
            print("wrapping method")
            call_log_params = CallLogParams(*args, **kwargs)
            return _wrap_function(wrapped, call_log_params)

    if outer_wrapped is None:
        print("outer wrapped is None")
        return decorate
    print("outerwrapped is not none")
    return decorate(outer_wrapped)
    

def log(magic: Union[Wrappable, Loggable]=None, *args,
        level: int=None,
        logger: logging.Logger=None,
        **kwargs) -> Union[Wrappable, None]:
    """catch-all log method of goatl
    
    # mymodule.py:
    >>> from goatl import log
    
    as a function, it can be used to log similar to the logging module
    
    >>> log("hello world")
    >>> # INFO:root:hello world
    
    >>> log.debug("hello world") # TODO: not sure if this is possible?
    >>> # DEBUG:root:hello world

    method wrapper: it will log the function call and return value 
    >>> @log
    >>> def foo(x):
    >>>     return x

    >>> foo(21)
    >>> # INFO:root:called foo with x=21
    >>> # DEBUG:root:foo returned 21
    
    class decorator: it will apply the log method to all methods of the class
    __init__ which will be logged as an initialization
    private methods (i.e methods starting with _) will not be logged by default
    property getters and setters will not be logged by default # TODO:decide on this
    
    >>> @log
    >>> class Foo:
    >>>     def __init__(self, x):
    >>>         self.x = x
    
    >>>     def bar(self):
    >>>         return self.x * 2
    
    >>> Foo(21).bar()
    >>> # INFO:root:Initialized Foo <@objectid>  with x=21
    >>> # INFO:root:called Foo.bar with self=<@objectid>
    >>> # DEBUG:root:Foo.bar returned 42

    method and class decoration is highly customizable
    few examples of possible customizations:
    
    # Custom log level:
    >>> @log(level="DEBUG", return_level="INFO")
    >>> def foo(x):
    >>>     return x * 2
    
    >>> foo(21)
    >>> # DEBUG:root:called foo with x=21
    >>> # INFO:root:foo returned 42
    
    # Custom log message for class one class method:
    >>> @log
    >>> class Foo:
    >>>     @log(message="[%(asctime)s] %(levelname)s: %(return)s from %(funcName)s")
    >>>    def bar(self):
    >>>         return 42
    
    >>> Foo().bar()
    >>> # [2021-01-01 00:00:00] INFO: 42 from Foo.bar

    see the documentation for more details
    Args:
    """
    print(f"{magic=}, {args=}, {kwargs=}")
    
    if isinstance(magic, Union[type, Callable]):
        print("Wrapping method or class")
        return _wrap(magic, **kwargs)
    else:
        Log(message=magic, level=level, logger=logger)(*args, **kwargs)

        
setattr(log, "info", functools.partial(log, level=logging.INFO))
setattr(log, "debug", functools.partial(log, level=logging.DEBUG))
setattr(log, "warning", functools.partial(log, level=logging.WARNING))
setattr(log, "error", functools.partial(log, level=logging.ERROR))
setattr(log, "critical", functools.partial(log, level=logging.CRITICAL))
    