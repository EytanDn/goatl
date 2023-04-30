import pytest
import logging
from goatl import logger

class ExceptionTest(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return "ExceptionTest"


class ShouldWarnError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return "ShouldWarnError"


@pytest.fixture(params=[(None), ExceptionTest])
def raise_exception(request):
    return request.param


@pytest.fixture(params=[(''), ("something")])
def print_something(request):
    return request.param


@pytest.fixture(params=[(None), (1), (0)])
def return_value(request):
    return request.param


@pytest.fixture
def func(return_value, print_something, raise_exception):

    def inner():
        if print_something:
            print(print_something)
        if raise_exception:
            raise raise_exception
        return return_value

    return {"func": inner,
            "return_value": return_value,
            "print_something": print_something,
            "raise_exception": raise_exception}


@pytest.fixture(params=[(None), (1), (0)])
def args_func(request):
    args = request.param

    def inner(*args):
        return args

    return {"func": inner,
            "args": args}


@pytest.fixture(params=[{"a": 1}, {"a": 1, "b": 2}])
def kwargs_func(request):
    kwargs = request.param

    def inner(**kwargs):
        return kwargs

    return {"func": inner,
            "kwargs": kwargs}


@pytest.fixture(params=[(logging.DEBUG), (logging.INFO), (logging.WARNING), (logging.ERROR)])
def level(request):
    return request.param


@pytest.fixture
def caplog(caplog):
    caplog.set_level(logging.DEBUG, logger=__name__)
    return caplog


@pytest.fixture(params=[True, False])
def with_parentheses(request):
    return request.param


class TestFuncLogDecorator:

    def test_log_decoration(self, with_parentheses, caplog):
        """Test that the log decorator works."""

        with caplog.at_level(logging.DEBUG, logger=logger.__name__):
            if with_parentheses:
                @logger.log()
                def func():
                    pass
            else:
                @logger.log
                def func():
                    pass

            assert "log decorator called" in caplog.text
            assert "decorating function func" in caplog.text
            assert "log decorator finished" in caplog.text

    def test_log_doesnt_meddle_func(self, func, caplog, capsys):
        """Test that the log decorator doesn't meddle with the function."""

        @logger.log
        def inner_func():
            return func["func"]()

        if func["raise_exception"]:
            with pytest.raises(func["raise_exception"]):
                inner_func()
        else:
            assert inner_func() is func["return_value"]

        capture = capsys.readouterr()
        assert capture.out.strip() == func['print_something']

    def test_log_doesnt_meddle_arg_func(self, args_func, caplog, capsys):
        """Test that the log decorator doesn't meddle with the function."""

        @logger.log
        def inner_func(*args):
            return args_func["func"](*args)

        assert inner_func(args_func["args"]) == (args_func["args"],)

    def test_log_desont_meddle_kwargs_func(self, kwargs_func, with_parentheses, caplog, capsys):
        """Test that the log decorator doesn't meddle with the function."""

        @logger.log
        def inner_func(**kwargs):
            return kwargs_func["func"](**kwargs)

        assert inner_func(**kwargs_func["kwargs"]) == kwargs_func["kwargs"]

    def test_log_doesnt_meddle_generator_func(self, caplog, capsys):
        """Test that the log decorator doesn't meddle with the function."""

        @logger.log
        def inner_func():
            yield 1
            yield 2

        assert list(inner_func()) == [1, 2]

    def test_log_loggings(self, func, caplog, capsys):
        """Test that the log decorator logs the correct messages."""

        @logger.log
        def inner_func():
            return func["func"]()

        if func["raise_exception"]:
            with pytest.raises(func["raise_exception"]):
                inner_func()
        else:
            inner_func()

        assert caplog.records[0].levelname == "INFO"

        if func["raise_exception"]:
            assert caplog.records[1].levelname == "ERROR"
        else:
            assert caplog.records[1].levelname == "DEBUG"

    def test_log_all_logs_go_to_level(self, caplog, level):

        @logger.log(level=level)
        def func():
            pass

        func()

        for record in caplog.records:
            assert record.levelno == level

    def test_log_level_and_another(self, caplog, level):

        @logger.log(level=logging.DEBUG, call=level)
        def func():
            pass

        func()
        assert caplog.records[0].levelno == level
        for record in caplog.records[1:]:
            assert record.levelno == logging.DEBUG


class TestClassLogDecorator:
    def test_log_decoration(self, with_parentheses, caplog):
        """Test that the log decorator works."""

        with caplog.at_level(logging.DEBUG, logger=logger.__name__):
            if with_parentheses:
                @logger.log()
                class Class:
                    pass
            else:
                @logger.log
                class Class:
                    pass

            assert "log decorator called" in caplog.text
            assert "decorating class Class" in caplog.text
            assert "log decorator finished" in caplog.text

    def test_log_doesnt_meddle_class(self, func, caplog, capsys):
        """Test that the log decorator doesn't meddle with the class."""

        class DummyClass:
            pass

        @logger.log
        class Class(DummyClass):
            def func(self):
                return func["func"]()

        instance = Class()
        
        assert isinstance(instance, Class)
        assert isinstance(instance, DummyClass)

        assert type(instance) is Class
        assert type(instance) is not DummyClass

        assert getattr(instance, "func") is not Class.func
        assert getattr(instance, "func").__name__ == "func"

        if func["raise_exception"]:
            with pytest.raises(func["raise_exception"]):
                instance.func()
        else:
            assert instance.func() is func["return_value"]

        capture = capsys.readouterr()
        assert capture.out.strip() == func['print_something']

    def test_log_level_to_members(self, caplog, level):

        @logger.log(level=level)
        class Class:
            def func(self):
                pass

        instance = Class()

        instance.func()

        for record in caplog.records:
            assert record.levelno == level

        assert len(caplog.records) == 3

    def test_different_levels_to_members(self, caplog, level):

        @logger.log(level=logging.DEBUG, call=level, return_=level)
        class Class:
            def func(self):
                pass

        instance = Class()

        caplog.clear()

        instance.func()

        for record in caplog.records:
            assert record.levelno == level

        assert len(caplog.records) == 2


class TestLevelDecorator:

    @staticmethod
    def assert_has_attrs(func, level) -> bool:
        return all([getattr(func, attr, False) for attr in
                ["_log_call_level",
                 "_log_return_level", 
                 "_log_error_level", 
                 "_log_warn_level", 
                 "_log_level"]])

    def test_level_decoration(self, level):

        @logger.level(level, level, level, level, level=level)
        def func():
            pass

        assert self.assert_has_attrs(func, level)

    def test_level_decoration_in_class(self, level):

        @logger.log(level=logging.NOTSET)
        class Class:
            def func2(self):
                pass

            @logger.level(level, level, level, level, level=level)
            def func(self):
                pass

        assert self.assert_has_attrs(Class.func, level)

    def test_level_logging(self, level, caplog):

        @logger.log
        class Class:

            @logger.level(call=level, return_=level)
            def func(self):
                pass

        with caplog.at_level(logging.INFO, logger=__name__):
            instance = Class()
            assert len(caplog.records) == 1
            caplog.clear()
            
        instance.func()
        
        for record in caplog.records:
            assert record.levelno == level
        
        assert len(caplog.records) == 2
        
    def test_level_no_log(self, level, caplog):

        @logger.log
        class Class:

            @logger.level(call=level, return_=False)
            def func(self):
                pass

            @logger.level(no_log=True)
            def func2(self):
                pass
            
        with caplog.at_level(logging.INFO, logger=__name__):
            instance = Class()
            assert len(caplog.records) == 1
            caplog.clear()
            
        with caplog.at_level(level, logger=__name__):
            instance.func()
            instance.func2()
            assert len(caplog.records) == 1

    def test_level_log_private_func(self, level, caplog):

        @logger.log
        class Class:

            @logger.level(call=level, return_=level)
            def _func(self):
                pass
            
            def _func2(self):
                pass

        with caplog.at_level(logging.INFO, logger=__name__):
            instance = Class()
            assert len(caplog.records) == 1
            caplog.clear()
            
        instance._func()
        instance._func2()
        
        for record in caplog.records:
            assert record.levelno == level
        
        assert len(caplog.records) == 2