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

        func()
        
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


        with caplog.at_level(logging.DEBUG):
            inner_func()
            assert caplog.records[0].message == "called inner_func with () {}"
            assert caplog.records[0].levelno == logging.INFO
            assert caplog.records[1].message == "inner_func returned %s" % func["return_value"]
            assert caplog.records[1].levelno == logging.DEBUG
            
        capture = capsys.readouterr()
        assert capture.out.strip() == func['print_something']
        

    def test_log_all_logs_go_to_level(self, caplog, level):

        @goatl.log(level=level)
        def func():
            pass

        with caplog.at_level(level):
            func()

            for record in caplog.records:
                assert record.levelno == level


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
                
        assert Class.__name__ == "Class"
        assert Class.__module__ == __name__

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

        with caplog.at_level(level):
            instance = Class()
            instance.func()

            assert caplog.records[0].message == "Initialized Class with () {}"
            assert caplog.records[1].message == "called func with (%s,) {}" % instance
            assert caplog.records[2].message == "func returned None"

            for record in caplog.records:
                assert record.levelno == level
                

    def test_private_method_no_log(self, caplog):

        @goatl.log
        class Class:
            def _func(self):
                pass
            
            def __str__(self):
                return "Class"

        instance = Class()

        caplog.clear()

        instance._func()
        str(instance)
        
        assert len(caplog.records) == 0
    
    def test_private_method_override_wrap(self, caplog):
        @goatl.log
        class Class:
            @goatl.log
            def _func(self):
                pass
            
        
        with caplog.at_level(logging.INFO):
            instance = Class()
            
            assert caplog.records[0].message == "Initialized Class with () {}"
            
        caplog.clear()
            
        with caplog.at_level(logging.DEBUG):
            instance._func()
            
            assert caplog.records[0].message == "called _func with (%s,) {}" % instance
            assert caplog.records[0].levelno == logging.INFO
            assert caplog.records[1].message == "_func returned None"
            assert caplog.records[1].levelno == logging.DEBUG
    
    def test_private_method_override_wrap_at_level(self, caplog, level):
        @goatl.log
        class Class:
            @goatl.log(level=level)
            def _func(self):
                pass
            
        
        with caplog.at_level(logging.INFO):
            instance = Class()
            
            assert caplog.records[0].message == "Initialized Class with () {}"
            
        caplog.clear()
            
        with caplog.at_level(level):
            instance._func()
            
            assert caplog.records[0].message == "called _func with (%s,) {}" % instance
            assert caplog.records[1].message == "_func returned None"
            
            for record in caplog.records:
                assert record.levelno == level

