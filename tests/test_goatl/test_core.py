import pytest
import logging
import goatl


@pytest.fixture(params=[(''), ("something")])
def print_something(request):
    return request.param

@pytest.fixture(params=[(None), (1), (0)])
def return_value(request):
    return request.param

@pytest.fixture
def func(return_value, print_something):

    def inner():
        if print_something:
            print(print_something)
        return return_value

    return {"func": inner,
            "return_value": return_value,
            "print_something": print_something}


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

    def test_log_decoration(self, with_parentheses):
        """Test that the log decorator works."""

        if with_parentheses:
            @goatl.log()
            def func():
                pass
        else:
            @goatl.log
            def func():
                pass

        assert func.__name__ == "func"
        assert func.__module__ == __name__

    def test_log_doesnt_meddle_func(self, func, caplog, capsys):
        """Test that the log decorator doesn't meddle with the function."""

        @goatl.log
        def inner_func():
            return func["func"]()

        assert inner_func() is func["return_value"]

        capture = capsys.readouterr()
        assert capture.out.strip() == func['print_something']

    def test_log_doesnt_meddle_arg_func(self, args_func, caplog, capsys):
        """Test that the log decorator doesn't meddle with the function."""

        @goatl.log
        def inner_func(*args):
            return args_func["func"](*args)

        assert inner_func(args_func["args"]) == (args_func["args"],)

    def test_log_desont_meddle_kwargs_func(self, kwargs_func, with_parentheses, caplog, capsys):
        """Test that the log decorator doesn't meddle with the function."""

        @goatl.log
        def inner_func(**kwargs):
            return kwargs_func["func"](**kwargs)

        assert inner_func(**kwargs_func["kwargs"]) == kwargs_func["kwargs"]

    def test_log_doesnt_meddle_generator_func(self, caplog, capsys):
        """Test that the log decorator doesn't meddle with the function."""

        @goatl.log
        def inner_func():
            yield 1
            yield 2

        assert list(inner_func()) == [1, 2]

    def test_log_loggings(self, func, caplog, capsys):
        """Test that the log decorator logs the correct messages."""

        @goatl.log
        def inner_func():
            return func["func"]()

        inner_func()

        assert caplog.records[0].levelname == "INFO"
        assert caplog.records[1].levelname == "DEBUG"

    def test_log_all_logs_go_to_level(self, caplog, level):

        @goatl.log(level=level)
        def func():
            pass

        func()

        for record in caplog.records:
            assert record.levelno == level

    def test_log_level_and_another(self, caplog, level):
        pass
        # @goatl.log(level=logging.DEBUG, call=level)
        # def func():
        #     pass

        # func()
        # assert caplog.records[0].levelno == level
        # for record in caplog.records[1:]:
        #     assert record.levelno == logging.DEBUG


class TestClassLogDecorator:
    def test_log_decoration(self, with_parentheses, caplog):
        """Test that the log decorator works."""

        with caplog.at_level(logging.DEBUG, logger=__name__):
            if with_parentheses:
                @goatl.log()
                class Class:
                    pass
            else:
                @goatl.log
                class Class:
                    pass


    def test_log_doesnt_meddle_class(self, func, caplog, capsys):
        """Test that the log decorator doesn't meddle with the class."""

        class DummyClass:
            pass

        @goatl.log
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

        assert instance.func() is func["return_value"]

        capture = capsys.readouterr()
        assert capture.out.strip() == func['print_something']

    def test_log_level_to_members(self, caplog, level):

        @goatl.log(level=level)
        class Class:
            def func(self):
                pass

        instance = Class()
        instance.func()

        for record in caplog.records:
            assert record.levelno == level

        assert len(caplog.records) == 3

    def test_different_levels_to_members(self, caplog, level):

        # @goatl.log(level=logging.DEBUG, call=level, return_=level)
        # class Class:
        #     def func(self):
        #         pass

        # instance = Class()

        # caplog.clear()

        # instance.func()

        # for record in caplog.records:
        #     assert record.levelno == level

        # assert len(caplog.records) == 2
        pass

