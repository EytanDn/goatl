import pytest
import logging
from goatl import log

def test_wrap():
    def test_func(x):
        return x * 2

    wrapped_func = log.wrap(test_func)
    assert callable(wrapped_func), "wrap should return a callable"

    result = wrapped_func(5)
    assert result == 10, "wrapped function should correctly execute original function"

def test_wrap_class():
    class TestClass:
        def method(self):
            return "Hello, World!"

    wrapped_class = log.wrap_class(TestClass)
    assert callable(wrapped_class), "wrap_class should return a callable"

    instance = wrapped_class()
    assert isinstance(instance, TestClass), "wrapped class should be instance of original class"

    result = instance.method()
    assert result == "Hello, World!", "methods of wrapped class should correctly execute original methods"

def test_log():
    # Assuming log.log returns a callable when passed a function
    def test_func(x):
        return x * 2

    logged_func = log.log(logging.INFO, test_func)
    assert callable(logged_func), "log.log should return a callable when passed a function"

    result = logged_func(5) # type: ignore
    assert result == 10, "logged function should correctly execute original function"

    # Assuming log.log returns None when passed a string
    result = log.log(logging.INFO, "Test message")
    assert result is None, "log.log should return None when passed a string"

# Repeat the test_log function for info, debug, warn, error, and critical