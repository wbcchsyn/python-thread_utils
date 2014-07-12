# -*- coding: utf-8 -*-

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
import time

import thread_utils

TEST_INTERVAL = 0.1
TEST_COUNT = 5


def test_function_simultaneous_access():
    """
    Only one thread can access to decorated function.
    """

    @thread_utils.synchronized
    def foo(n):
        time.sleep(n)

    threads = [threading.Thread(target=foo, args=(TEST_INTERVAL,))
               for i in xrange(TEST_COUNT)]

    start = time.time()
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert (time.time() - start) > TEST_INTERVAL * TEST_COUNT


def test_method_simultaneous_access():
    """
    Only one thread can access to decorated method.
    """

    class Foo(object):
        @thread_utils.synchronized
        def bar(self, n):
            time.sleep(n)

    # Call method of the same object.
    foo = Foo()
    threads = [threading.Thread(target=foo.bar, args=(TEST_INTERVAL,))
               for i in xrange(TEST_COUNT)]

    start = time.time()
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert (time.time() - start) > TEST_INTERVAL * TEST_COUNT

    #  same method of various objects.
    threads = [threading.Thread(target=Foo().bar, args=(TEST_INTERVAL,))
               for i in xrange(TEST_COUNT)]

    start = time.time()
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert (time.time() - start) > TEST_INTERVAL * TEST_COUNT


def test_class_method_simultaneous_access():
    """
    Only one thread can access to decorated class method.
    """

    class Foo(object):
        @classmethod
        @thread_utils.synchronized
        def bar(cls, n):
            time.sleep(n)

    threads = [threading.Thread(target=Foo.bar, args=(TEST_INTERVAL,))
               for i in xrange(TEST_COUNT)]

    start = time.time()
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert (time.time() - start) > TEST_INTERVAL * TEST_COUNT


def test_static_method_simultaneous_access():
    """
    Only one thread can access to decorated static method.
    """

    class Foo(object):
        @staticmethod
        @thread_utils.synchronized
        def bar(n):
            time.sleep(n)

    threads = [threading.Thread(target=Foo.bar, args=(TEST_INTERVAL,))
               for i in xrange(TEST_COUNT)]

    start = time.time()
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert (time.time() - start) > TEST_INTERVAL * TEST_COUNT
