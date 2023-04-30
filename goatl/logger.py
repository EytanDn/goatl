import logging
from logging import(
    DEBUG, INFO, WARNING, ERROR, CRITICAL, 
    StreamHandler, Logger, Formatter,)
import functools
import inspect
from typing import Callable

# TODO: add handler configuration to decorator
logging.basicConfig(handlers=[StreamHandler()], level=INFO)

_logger = logging.getLogger(__name__) # please avoid confusion

###
# unimplemented
# - message specific formatting decorators
# - handler configuration
###

def message(message: str, *args, **kwargs) -> str:
    """Format a message."""
    pass

def call_message(message: str, *args, **kwargs) -> str:
    """Format a call message."""
    pass

def return_message(message: str, *args, **kwargs) -> str:
    """Format a return message."""
    pass

def error_message(message: str, *args, **kwargs) -> str:
    """Format an error message."""
    pass

def init_message(message: str, *args, **kwargs) -> str:
    """Format an initialization message."""
    pass

 ####

def level(call: int= None, return_: int=None, error:int = None, warning:int = None, *, level:int = None, no_log: bool= False) -> Callable:
    """Decorator to set the logging level of a function."""
    _logger.debug("level decorator called")
    def decorate(func: Callable) -> Callable:
        nonlocal return_, error, level
        setattr(func, "_log_marked", True)
        
        if level is not None:
            setattr(func, "_log_level", level)
        if call is not None:
            setattr(func, "_log_call_level", call)
        if return_ is not None:
            setattr(func, "_log_return_level", return_)
        if error is not None:
            setattr(func, "_log_error_level", error)
        if warning is not None:
            setattr(func, "_log_warn_level", warning)
        if no_log:
            setattr(func, "_no_log", no_log)
            
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    
    return decorate

def log(outer_wrapped = None,*, 
        logger: str | Logger=None, 
        level: int=None,
        call: int=None,
        return_: int=None,
        error: int=None,
        warning: int=None,
        init: int=None,
        warn_for: tuple= (),
        **logger_kwargs) -> Callable:
    """Decorator to log function calls.
    
    Args:
        wrapped: Function or class to decorate.
        logger: Logger to log to. If None, the logger of the module of the function is used.
        level: Logging level. Defaults to logging.DEBUG.
        ret: Logging level for return values. If None, the value of level is used.
        error: Logging level for exceptions. If None, the value of level is used.
        kwargs: Additional keyword arguments to be passed to the logger.
        
    Returns:
        Decorated function.
    """
    _logger.debug("log decorator called")
    
    def decorate(wrapped):
        if getattr(wrapped, "_no_log", False):
            return wrapped
        
        nonlocal logger, level, error, return_, warning, call, init

        if isinstance(logger, str):
            logger = logging.getLogger(logger)
        elif logger is None:
            logger = logging.getLogger(wrapped.__module__)

        if not isinstance(logger, Logger):
            raise TypeError(f"logger must be a string or a logging.Logger, not {type(logger)}")

        level = getattr(wrapped, "_log_level", level)
        
        call = getattr(wrapped, "_log_call_level", call) # TODO: refactor to an external method or class
        return_ = getattr(wrapped, "_log_return_level", return_)
        error = getattr(wrapped, "_log_error_level", error)
        warning = getattr(wrapped, "_log_warn_level", warning)
        init = getattr(wrapped, "_log_init_level", init)
        
        if level is not None:
            call = call if call is not None else level
            return_ = return_ if return_ is not None else level
            error = error if error is not None else level
            warning = warning if warning is not None else level
            init = init if init is not None else level
        
        call = call if call is not None else INFO
        return_ = return_ if return_ is not None else DEBUG
        error = error if error is not None else ERROR
        warning = warning if warning is not None else WARNING
        init = init if init is not None else INFO
        
        logger_kwargs.setdefault("stacklevel", 2)
        
        if inspect.isclass(wrapped):
            _logger.debug(f"decorating class {wrapped.__name__}")
            
            global ClassWrapper
            
            class ClassWrapper(wrapped):
                def __init__(self, *args, **kwargs):
                    logger.log(init, f"Instantiating {wrapped.__name__} with args {args} and kwargs {kwargs}", **logger_kwargs)
                    super().__init__(*args, **kwargs)
                
                def __getattribute__(self, name):
                    member = super().__getattribute__(name)
                    if getattr(member, "_log_marked", None):
                        return log(outer_wrapped=member, logger=logger, level=level, call=call, return_=return_, error=error, init=init, warning=warning, **logger_kwargs)
                    if name.startswith("_"):
                        return member
                    if inspect.ismethod(member):
                        return log(outer_wrapped=member, logger=logger, level=level, call=call, return_=return_, error=error, init=init, warning=warning, **logger_kwargs)
                    return member
            
            return ClassWrapper
            
            # @functools.wraps(wrapped)
            # def class_wrapper(*args, **kwargs):
            #     """ Log class instantiation and method calls."""
            #     logger.log(init, f"Instantiating {wrapped.__name__} with args {args} and kwargs {kwargs}", **logger_kwargs)
            #     instance = wrapped(*args, **kwargs)
            #     for name, member in inspect.getmembers(instance, inspect.ismethod):
            #         if getattr(member, "_log_marked", None):
            #             setattr(instance, name, log(outer_wrapped=member, logger=logger, level=level, call=call, return_=return_, error=error, init=init, warning=warning, **logger_kwargs))
            #             continue
            #         if name.startswith("_"):
            #             continue
            #         setattr(instance, name, log(outer_wrapped=member, logger=logger, level=level, call=call, return_=return_, error=error, init=init, warning=warning,  **logger_kwargs))
            #     return instance
            # return class_wrapper
        else:
            _logger.debug(f"decorating function {wrapped.__name__}")
            @functools.wraps(wrapped)
            def func_wrapper(*args, **kwargs):
                """Log function calls and return values."""
                if call:
                    logger.log(call, f"Calling {wrapped.__name__} with args {args} and kwargs {kwargs}", **logger_kwargs)
                try:
                    result = wrapped(*args, **kwargs)
                except warn_for as e:
                    if warning: 
                        logger.log(warning, f"Exception {e} raised by {wrapped.__name__} as warning", **logger_kwargs)
                except Exception as e:
                    if error:
                        logger.log(error, f"Exception {e} raised by {wrapped.__name__}", **logger_kwargs)
                    raise e
                else:
                    if return_:
                        if result is None:
                            ret_message =  f"{wrapped.__name__} returned None"
                        elif inspect.isgenerator(result):
                            ret_message = f"{wrapped.__name__} returned a generator"
                        else:
                            ret_message = f"{wrapped.__name__} returned {result}"
                        logger.log(return_, ret_message, **logger_kwargs)
                    return result
        return func_wrapper
    
    _logger.debug("log decorator finished")
    if outer_wrapped is None:
        return decorate
    return decorate(outer_wrapped)