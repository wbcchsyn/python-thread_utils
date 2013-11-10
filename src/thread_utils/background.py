#-*- coding: utf-8 -*-

import threading
import functools
import operator

import _gc
import _future


def background(daemon=True):
    """
    Decorator to create a worker thread and make method or function call there.

    Decorated function or method create a worker thread and return a future
    object immediately. The original function or method start to run in the
    worker thread.

    The worker progress and the result - either normal return value or
    unhandled exception can be seen through the future object to be returned
    by decorated function or method.

    See thread_utils._future.Future document for information about
    what returned by decorated function or method.

    This method can't decorate classmethod nor staticmethod.
    In such case, make classmethod or staticmethod after decorate with this
    like as follows.

    >> class Foo(object):
    >>     @classmethod
    >>     @background.
    >>     def foo(self, val):
    >>         return val

    This decorator doesn't affect to thread safty, so it depends on the
    original function or method whether decorated function or method will be
    thread safe or not.
    """

    daemon = operator.truth(daemon)

    def decorator(func):

        # Argument Check
        if not callable(func):
            raise TypeError("The 1st argument 'func' is requested "
                            "to be callable.")

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            def run(*args, **kwargs):
                try:
                    ret = func(*args, **kwargs)
                    future._set_return(ret)

                except BaseException as e:
                    future._set_error(e)

                finally:
                    _gc.put(threading.current_thread())

            t = threading.Thread(target=run, args=args, kwargs=kwargs)
            future = _future.Future()

            t.daemon = daemon
            t.start()

            return future

        return wrapper

    return decorator


def bg(daemon=True):
    """
    Alias for background(daemon=True)
    """

    return background(daemon)
