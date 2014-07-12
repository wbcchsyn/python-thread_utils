# -*- coding: utf-8 -*-

import threading
import functools
import operator

import _gc
import _future


def async(daemon=True):
    """
    Decorator that creates a worker thread and invokes callable there.

    Decorated callable object returns a Future object immediately and invoked
    callable starts to run in worker thread. If argument `daemon' is True,
    the worker thread will be daemonic; otherwise not. Python program exits
    when only daemon threads are left.

    In the following example, function sleep_sort print positive numbers in
    asending order. The main thread will terminate soon, however workers
    display numbers after that.

       import thread_utils
       import time

       @thread_utils.async(daemon=False)
       def _sleep_print(n):
           time.sleep(n)
           print n

       def sleep_sort(un_sorted_list):
           for i in un_sorted_list:
               _sleep_print(i)

       sleep_sort([3,1,4,2]) # Numbers are displayed in asending this order.

    The decorated callable returns a Future object immediately; it monitors
    invoked callable progress and stores the result. The foreground thread can
    access to the result of invoked callable through the future object like as
    follows.

       import thread_utils
       import time

       @thread_utils.async(daemon=True)
       def add(m, n):
           time.sleep(m)
           return m + n

       future = add(3, 5)
       print "Task started"
       print future.receive() # Blocks for 3 seconds and display "8".


    See help(thread_utils.Future) for more information about it.

    This function decorates only function and method. In case of classmethod or
    staticmethod, decorating with this method before make classmethod or
    staticmethod.

    This method can't decorate classmethod nor staticmethod.
    In such case, make classmethod or staticmethod after decorate with this.

       import thread_utils

       class Foo(object):
           @classmethod
           @thread_utils.async(daemon=False)
           def foo(cls):
               pass

    This decorator doesn't affect to thread safty, so it depends on the invoked
    callable whether decorated will be thread safe or not.
    """

    daemon = operator.truth(daemon)

    def decorator(func):

        # Argument Check
        if not callable(func):
            raise TypeError("The 1st argument 'func' is requested "
                            "to be callable.")

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            def run():
                try:
                    future._run()
                finally:
                    _gc._put(threading.current_thread())

            t = threading.Thread(target=run)
            future = _future.Future._create(func, *args, **kwargs)

            t.daemon = daemon
            t.start()

            return future

        return wrapper

    return decorator
