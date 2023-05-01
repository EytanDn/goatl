# goatl

```
some body please prompt midjourney for "Cartoonish goat scribing on a long scroll oil painting, --ar  2:1"
and make abanner for here.
```

##

<div align="center">

[![Build status](https://github.com/EytanDn/goatl/workflows/build/badge.svg?branch=master&event=push)](https://github.com/EytanDn/goatl/actions?query=workflow%3Abuild)
[![Python Version](https://img.shields.io/pypi/pyversions/goatl.svg)](https://pypi.org/project/goatl/)
[![Dependencies Status](https://img.shields.io/badge/dependencies-up%20to%20date-brightgreen.svg)](https://github.com/EytanDn/goatl/pulls?utf8=%E2%9C%93&q=is%3Apr%20author%3Aapp%2Fdependabot)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/EytanDn/goatl/blob/master/.pre-commit-config.yaml)
![Coverage Report](assets/images/coverage.svg)

</div>

## Installation

```bash
pip install -U goatl
```

or install with `Poetry`

```bash
poetry add goatl
```

## Purpose

goatl provides a simple and easy to use logging interface for python projects.
by replacing repetitive boilerplate code with a simple function call:
the magic "log" function.

```python
from goatl import log
```

### main features

the log function provides an easy interace for:

- out of and in context log calls
- wrapping existing functions with log calls
- wrapping existing classes with log calls
- logging configuration #not implemented yet

all in an intuitive and pythonic way.

## Usage

goatl usage is all about the log

### as a function

```python
log("hello world")
# 2020-07-19 16:00:00,000 - goatl - INFO - hello world
log.debug("hello world?")
# 2020-07-19 16:00:00,000 - goatl - DEBUG - hello world?
log.info("do you know the answer of {} + {}?", 41, 1)
# 2020-07-19 16:00:00,000 - goatl - INFO - do you know the answer of 41 + 1?
```

### as a method decorator

```python
@log
def foo(x, y):
    return x + y

@log.debug
def bar():
    return "hello world"

@log.debug(return_level=log.info)
def baz(x):
    return x*2

foo(1, 2)
# ... INFO - foo called with args: (1, 2), kwargs: {}
# ... DEBUG - foo returned: 3
bar()
# ... DEBUG - bar called with args: (), kwargs: {}
# ... INFO - bar returned: hello world
baz(3)
# ... DEBUG - baz called with args: (3,), kwargs: {}
# ... INFO - baz returned: 6
```

### as a class decorator

```python
@log
class Foo:
    def __init__(self, x):
        self.x = x

    def bar(self, y):
        return self.x + y

    @log.warn
    def baz(self):
        return self.x * 2


foo = Foo(1)
# ... INFO - Instantiated Foo with args: (1,), kwargs: {}
foo.bar(2)
# ... INFO - Foo.bar called with args: (2,), kwargs: {}
# ... DEBUG - Foo.bar returned: 3
foo.baz()
# ... WARNING - Foo.baz called with args: (), kwargs: {}
# ... WARNING - Foo.baz returned: 2
```

## Releases

You can see the list of available releases on the [GitHub Releases](https://github.com/EytanDn/goatl/releases) page.

## License

[![License](https://img.shields.io/github/license/Eytandn/goatl)](https://github.com/EytanDn/goatl/blob/master/LICENSE)

This project is licensed under the terms of the `MIT` license. See [LICENSE](https://github.com/eytandn/goatl/blob/master/LICENSE) for more details.

## Citation

```bibtex
@misc{goatl,
  author = {goatl},
  title = {Greatest of all time logger},
  year = {2023},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/EytanDn/goatl}}
}
```
