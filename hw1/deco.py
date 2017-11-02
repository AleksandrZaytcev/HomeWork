#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import update_wrapper


def disable(func):
    """
    Disable a decorator by re-assigning the decorator's name
    to this function. For example, to turn off memoization:

    >>> memo = disable
    """
    return func


def decorator(deco):
    """
    Decorate a decorator so that it inherits the docstrings
    and stuff from the function it's decorating.
    """

    def wrapper(func):
        return update_wrapper(deco(func), func)

    return update_wrapper(wrapper, deco)


@decorator
def count_calls(func):
    """Decorator that counts calls made to the function decorated."""

    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        return func(*args, **kwargs)

    wrapper.calls = 0
    return wrapper


@decorator
def memo(func):
    """
    Memoize a function so that it caches all return values for
    faster future lookups.
    """

    def wrapper(*args, **kwargs):
        update_wrapper(wrapper, func)
        key = args, frozenset(kwargs.items()) if kwargs else args
        if key in wrapper.cache:
            return wrapper.cache[key]
        res = wrapper.cache[key] = func(*args, **kwargs)
        return res

    wrapper.cache = {}
    return wrapper


@decorator
def n_ary(func):
    """
    Given binary function f(x, y), return an n_ary function such
    that f(x, y, z) = f(x, f(y,z)), etc. Also allow f(x) = x.
    """

    def wrapper(x, *args):
        return x if not args else func(x, wrapper(*args))

    return wrapper


def trace(fill_value):
    """Trace calls made to function decorated.

    @trace("____")
    def fib(n):
        ....

    >>> fib(3)
     --> fib(3)
    ____ --> fib(2)
    ________ --> fib(1)
    ________ <-- fib(1) == 1
    ________ --> fib(0)
    ________ <-- fib(0) == 1
    ____ <-- fib(2) == 2
    ____ --> fib(1)
    ____ <-- fib(1) == 1
     <-- fib(3) == 3

    """

    @decorator
    def tracer(func):
        def wrapper(*args):
            prefix = fill_value * wrapper.level
            fags = ", ".join(str(a) for a in args)
            print "{} --> {}({})".format(prefix, func.__name__, fags)
            wrapper.level += 1
            result = func(*args)
            print "{} <-- {}({}) == {}".format(prefix, func.__name__, fags, result)
            wrapper.level -= 1
            return result

        wrapper.level = 0
        return wrapper

    return tracer



@memo
@count_calls
@n_ary
def foo(a, b):
    return a + b


@count_calls
@memo
@n_ary
def bar(a, b):
    return a * b


@count_calls
@trace("####")
@memo
def fib(n):
    return 1 if n <= 1 else fib(n - 1) + fib(n - 2)


def main():
    print foo(4, 3)
    print foo(4, 3, 2)
    print foo(4, 3)
    print "foo was called", foo.calls, "times"

    print bar(4, 3)
    print bar(4, 3, 2)
    print bar(4, 3, 2, 1)
    print "bar was called", bar.calls, "times"

    print fib.__doc__
    fib(3)
    print fib.calls, 'calls made'


if __name__ == '__main__':
    main()
