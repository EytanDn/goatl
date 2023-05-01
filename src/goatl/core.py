import logging
import inspect
import functools
from dataclasses import dataclass, field
from typing import Callable, Optional, Union, TypeVar

import sys
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
        # TODO: warning maybe if not all args and kwargs are formatted? or missing?
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
        if isinstance(self.level, str):
            self.level = getattr(logging, self.level.upper())       
        elif self.level in log.levels:
            self.level = log.levels[self.level]
        
        if self.level is None:
            _logger.warning(f"level is None, using default level {DEFAULT_CALL_LEVEL}")
            self.level = DEFAULT_CALL_LEVEL
        
        self.message = self.message or DEFAULT_CALL_MESSAGE
        self.logger = self.logger or logging.getLogger()
    
    def __call__(self, *args, **kwargs) -> None:
        """log the message"""
        args = (*self.args, *args)
        kwargs = {**self.kwargs, **kwargs}
        self.logger.log(self.level, BraceMessage(self.message, *args, **kwargs))
    
    @staticmethod
    def _from_kwargs(kwargs: dict, 
                    default_message: str, 
                    default_level: int,
                    prefix: str) -> "Log | None":
        
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
                
        return Log(message=message, level=level, logger=kwargs.get("logger", None))
    
@dataclass
class CallLogParams:
    kwargs: Optional[dict] = field(default_factory=dict)

    def __post_init__(self): # TODO: seperate between level, call_level, reutrn_level
        # if call_message is present use it, else use message if present, else use default
        # if call_level is present use it, else use level if present, else use default

        self.call_log = Log._from_kwargs(self.kwargs, 
                                          DEFAULT_CALL_MESSAGE, 
                                          DEFAULT_CALL_LEVEL,
                                          prefix="call") 
        self.return_log = Log._from_kwargs(self.kwargs, 
                                        DEFAULT_RETURN_MESSAGE,
                                        DEFAULT_RETURN_LEVEL,
                                        prefix="return")

@dataclass
class ClassLogParams:
    kwargs: Optional[dict] = field(default_factory=dict)

    def __post_init__(self):
        self.method_log: Optional[CallLogParams] = CallLogParams(kwargs=self.kwargs)
        self.private_log: Optional[CallLogParams] = None
        self.property_log: Optional[CallLogParams] = None
        self.init_log: Optional[Log] = Log._from_kwargs(self.kwargs, 
                                                         DEFAULT_INIT_MESSAGE,
                                                         DEFAULT_INIT_LEVEL,
                                                         prefix="init")
        
        if any([key.startswith("private") 
                for key, value in self.kwargs.items() 
                if value is not None]):
            p_kwargs = {
                "message": self.kwargs.get("private_message", None),
                "level": self.kwargs.get("private_level", None)
            }
            self.private_log = CallLogParams(kwargs={**self.kwargs, **p_kwargs})
            
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

def _transfer_class_meta(wrapped: type, wrapper: type) -> type:
    """transfer meta data from wrapped to wrapper"""
    wrapper.__name__ = wrapped.__name__
    wrapper.__module__ = wrapped.__module__
    wrapper.__qualname__ = wrapped.__qualname__
    wrapper.__doc__ = wrapped.__doc__
    wrapper.__annotations__ = wrapped.__annotations__
    
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
    
    return _transfer_class_meta(wrapped, Wrapper)

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
    else: # TODO: maybe seperate between class kwargs and function kwargs
        call_log_params = CallLogParams(kwargs)
        return _wrap_function(wrapped, call_log_params)


def log(magic: Union[Wrappable, Loggable]=None, /,
        *args,
        message: Optional[str]=None,
        level: Optional[int]=None,
        logger: Optional[logging.Logger]=None,
        call_message: Optional[str]=None,
        call_level: Optional[int]=None,
        return_message: Optional[str]=None,
        return_level: Optional[int]=None,
        init_message: Optional[str]=None,
        init_level: Optional[int]=None,
        private_message: Optional[str]=None,
        private_level: Optional[int]=None,
        property_message: Optional[str]=None,
        property_level: Optional[int]=None,
        **kwargs) -> Union[Wrappable, None]:
    """catch-all log method of goatl
    
    ## mymodule.py:
    >>> from goatl import log
        
    ### function:
    log can be used in a similar to the logging module
    
    >>> log("hello world")
    ... # INFO:root:hello world
    
    >>> log.debug("hello world")
    ... # DEBUG:root:hello world 

    # ### method wrapper: 
    # it will log the function call and return value
    
    >>> @log
    ... def foo(x):
    ...    return x * 2
    >>> foo(21)
    42
    >>> # INFO:root:called foo with x=21
    >>> # DEBUG:root:foo returned 42
    
    ### class decorator: 
    it will apply the log method to all methods of the class
    __init__ which will be logged as an initialization
    private methods (i.e methods starting with _) will not be logged by default
    property getters and setters will not be logged by default # TODO:decide on this
    
    
    >>> @log
    ... class Foo:
    ...    def __init__(self, x):
    ...        self.x = x
    ...    def foo(self):
    ...        return self.x * 2 
    >>> f = Foo(21)
    ... # INFO:root:initialized Foo with x=21
    >>> f.foo()
    42
    >>> # INFO:root:called Foo.foo with self=<__main__.Foo object at 0x7f9b1c0e5a90>
    >>> # DEBUG:root:Foo.foo returned 42
    
    ## Customization
    method and class decoration is highly customizable
    few examples of possible customizations:
    
    ### Custom log level:
    >>> @log.debug(return_level="INFO")
    ... def foo(x):
    ...     return x * 2
    >>> foo(21)
    42
    >>> # DEBUG:root:called foo with x=21
    >>> # INFO:root:foo returned 42
    
    ### Custom log message for class one class method:
    >>> @log
    ... class Bar:
    ...     @log.info(return_message="[%(asctime)s] %(levelname)s: %(return)s from %(funcName)s")
    ...     def bar(self):
    ...         return 42
    >>> Bar().bar()
    42
    >>> # [2021-01-01 00:00:00] INFO: 42 from Foo.bar

    see the documentation for more details
    Args:
    """
    
        
    if isinstance(magic, Union[type, Callable, type(None)]):
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
            return _wrap(wrapped, **log_kwargs, **kwargs)
        
        if magic is None:
            return decorate
        return decorate(magic)
    else:
        if level is None: # TODO: maybe search for level in current score?
            level = logging.INFO
        
        Log(message=magic, level=level, logger=logger)(*args, **kwargs)

info: Callable = functools.partial(log, level=logging.INFO)
setattr(log, "info", info)
debug: Callable = functools.partial(log, level=logging.DEBUG)
setattr(log, "debug", debug)
warning: Callable = functools.partial(log, level=logging.WARNING)
setattr(log, "warning", warning)  
error: Callable = functools.partial(log, level=logging.ERROR)
setattr(log, "error", error)
critical: Callable = functools.partial(log, level=logging.CRITICAL)
setattr(log, "critical", critical)

levels: dict[Callable, int] = {
    info: logging.INFO,
    debug: logging.DEBUG,
    warning: logging.WARNING,
    error: logging.ERROR,
    critical: logging.CRITICAL
}

setattr(log, "levels", levels)