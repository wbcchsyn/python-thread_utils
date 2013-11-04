#!-*- coding: utf-8 -*-

import sys
sys.path.append('src')

import pytest
import threading
import time

import thread_utils


TEST_INTERVAL = 0.1
TEST_COUNT = 5

SAMPLE_RESULTS = [0, 3, True, False, "FOO", "", None, object(), Exception()]
SAMPLE_EXCEPTIONS = [Exception(), RuntimeError("Foo")]


class TestReceiveWhatReturnedInBackground(object):
    """
    What is returned in background can be accessible from foreground.

    Decorated method or function returns a future object and
    future.receive() returns what is returned in background.
    """

    def test_receive_what_function_returned_in_background(self):
        """
        future.receive() returns what function returned in background.
        """

        @thread_utils.bg()
        def foo(ret):
            return ret

        for ret in SAMPLE_RESULTS:
            assert ret is foo(ret).receive()

    def test_receive_what_method_returned_in_background(self):
        """
        future.receive() returns what method returned in background.
        """

        class Foo(object):

            @thread_utils.bg()
            def bar(self, n):
                return n

        for ret in SAMPLE_RESULTS:
            assert ret is Foo().bar(ret).receive()

    def test_receive_what_classmethod_returned_in_background(self):
        """
        future.receive() returns what classmethod returned in background.
        """

        class Foo(object):

            @classmethod
            @thread_utils.bg()
            def bar(cls, n):
                return n

        for ret in SAMPLE_RESULTS:
            assert ret is Foo.bar(ret).receive()
            assert ret is Foo().bar(ret).receive()

    def test_receive_returns_what_staticmethod_returned_in_background(self):
        """
        future.receive() returns what staticmethod returned in background.
        """

        class Foo(object):

            @staticmethod
            @thread_utils.bg()
            def bar(n):
                return n

        for ret in SAMPLE_RESULTS:
            assert ret is Foo.bar(ret).receive()
            assert ret is Foo().bar(ret).receive()


class TestReceiveWhatRaisedInBackground(object):
    """
    Exception raised in background is raised in foreground.

    Decorated method or function returns a future object and
    future.receive() returns what is returned in background.
    """

    def test_receive_raises_what_function_raised_in_background(self):
        """
        future.receive() raises what function raised in background.
        """

        @thread_utils.bg()
        def foo(e):
            raise e

        for exception in SAMPLE_EXCEPTIONS:
            try:
                foo(exception)
            except Exception as e:
                assert exception is e

    def test_receive_raises_what_method_raised_in_background(self):
        """
        future.receive() raises what method raised in background.
        """

        class Foo(object):
            @thread_utils.bg()
            def bar(self, e):
                raise e

        for exception in SAMPLE_EXCEPTIONS:
            try:
                Foo().bar(exception)
            except Exception as e:
                assert exception is e

    def test_receive_raises_what_classfunction_raised_in_background(self):
        """
        future.receive() raises what classfunction raised in background.
        """

        class Foo(object):
            @classmethod
            @thread_utils.bg()
            def bar(cls, e):
                raise e

        for exception in SAMPLE_EXCEPTIONS:
            try:
                Foo.bar(exception)
            except Exception as e:
                assert exception is e

    def test_receive_raises_what_staticmethod_raised_in_background(self):
        """
        future.receive() raises what staticmethod raised in background.
        """

        class Foo(object):
            @staticmethod
            @thread_utils.bg()
            def bar(e):
                raise e

        for exception in SAMPLE_EXCEPTIONS:
            try:
                Foo.bar(exception)
            except Exception as e:
                assert exception is e


def test_worker_thread_was_joined_by_gc():
    """
    Worker thread is joined automatically after finished.
    """

    @thread_utils.bg()
    def foo():
        pass

    # Wait for threads of another test will be joined.
    time.sleep(TEST_INTERVAL)

    active_threads = threading.active_count()
    [foo() for i in xrange(TEST_COUNT)]

    # Wait for threads are joined.
    time.sleep(TEST_INTERVAL)
    assert threading.active_count() == active_threads


def test_worker_is_daemonic_unless_specified():
    """
    Worker thread is daemonic in default, but it can be specified.
    """

    def foo():
        return threading.current_thread().daemon

    default = thread_utils.bg()(foo)
    daemonic = thread_utils.bg(daemon=True)(foo)
    non_daemonic = thread_utils.bg(daemon=False)(foo)

    assert default().receive()
    assert daemonic().receive()
    assert not non_daemonic().receive()


def test_receive_raises_TimeoutError_if_task_do_not_finish_before_timeout():
    """
    future.receive() raises TimeoutError if task won't finish before timeout.
    """

    event = threading.Event()
    event.clear()

    @thread_utils.bg()
    def foo():
        event.wait()

    with pytest.raises(thread_utils.TimeoutError):
        foo().receive(timeout=TEST_INTERVAL)

    event.set()


def test_is_finished_returns_whether_task_is_finished_or_not():
    """
    is_finished() returns whether task is finished or not.
    """

    event = threading.Event()
    event.clear()

    @thread_utils.bg()
    def foo():
        event.wait()

    f = foo()

    time.sleep(TEST_INTERVAL)
    assert not f.is_finished()

    event.set()
    time.sleep(TEST_INTERVAL)
    assert f.is_finished()
