# -*- coding: utf-8 -*-
'''
Copyright 2014, 2015 Yoshida Shin

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''


import threading
import functools

__MODULE_LOCK = threading.Lock()
__METHOD_LOCKS = {}


def synchronized(func):
    """
    Decorator to restrict from simultaneous access from 2 or more than 2
    threads.

    Decorated callable can be accessible from only one thread. If 2 or more
    than 2 threads try calling at the same time, only the 1st thread starts
    to run and the others are blocked. It is after the 1st thread finishes when
    2nd threads starts to run.

    In the following example, text "Worker is started" will printed 10 times
    at once. On the other hand, "Worker is finished" will printed every second.

       import thread_utils
       import time

       @thread_utils.synchronized
       def foo():
           time.sleep(1)

       @thread_utils.async(daemon=False)
       def create_worker():
           print "Worker is started."
           foo()
           print "Worker is finished."

       for i in xrange(10):
           create_worker()

    This function decorates only functino or method. In case of classmethod or
    staticmethod, decorating with this method before make classmethod or
    staticmethod.

       class Foo(object):
           @staticmethod
           @thread_utils.synchronized
           def foo():
               pass
    """

    # Argument Check
    if not callable(func):
        raise TypeError("The argument 'func' is required to be callable.")

    # Create the method Lock.
    with __MODULE_LOCK:
        if not id(func) in __METHOD_LOCKS:
            __METHOD_LOCKS[id(func)] = threading.Lock()

    # Acquire the Lock object and execute the funaction.
    # Only the following function runs when called.
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with __METHOD_LOCKS[id(func)]:
            return func(*args, **kwargs)

    return wrapper
