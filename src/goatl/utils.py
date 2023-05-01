from typing import Callable


def _transfer_class_meta(wrapped: type, wrapper: type) -> type:
    """transfer meta data from wrapped to wrapper"""
    wrapper.__name__ = wrapped.__name__
    wrapper.__module__ = wrapped.__module__
    wrapper.__qualname__ = wrapped.__qualname__
    wrapper.__doc__ = wrapped.__doc__
    wrapper.__annotations__ = wrapped.__annotations__
    
    return wrapper


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