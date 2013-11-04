# -*- coding: utf-8 -*-

import threading
import functools

__MODULE_LOCK = threading.Lock()
__METHOD_LOCKS = {}


def synchronized(func):
    """
    Decorator to restrict simultaneous access from 2 or more than 2 threads.
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
