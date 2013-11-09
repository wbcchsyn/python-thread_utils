#-*- coding: utf-8 -*-

import threading
import functools
import operator

import _gc
import _future


def background(daemon=True):

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
    return background(daemon)
