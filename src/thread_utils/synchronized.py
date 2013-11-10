# -*- coding: utf-8 -*-

import threading
import functools

__MODULE_LOCK = threading.Lock()
__METHOD_LOCKS = {}


def synchronized(func):
    """
    Decorator to restrict simultaneous access from 2 or more than 2 threads.

    Decorated function or method can be accessible from only one thread.
    If 2 or more than 2 threads try to call decorated function or method
    at the same time, only the 1st thread start to execute it and the others
    are waiting. It is after the 1st thread finishes when 2nd thread starts
    to do it.

    This method can't decorate classmethod nor staticmethod.
    In such case, make classmethod or staticmethod after decorate with this
    like as follows.

    >> class Foo(object):
    >>     @classmethod
    >>     @synchronized
    >>     def foo(val):
    >>         return val
    """

    # Argument Check
    if not callable(func):
        raise TypeError("The argument 'func' is required to be callable.")

    # Create the method Lock.
    with __MODULE_LOCK:
        if not id(func) in __METHOD_LOCKS:
            __METHOD_LOCKS[id(func)] = threading.Lock()

    # Acquire the Lock object and execute the funaction.
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with __METHOD_LOCKS[id(func)]:
            return func(*args, **kwargs)

    return wrapper
