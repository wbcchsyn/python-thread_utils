# -*- coding: utf-8 -*-

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import threading
import thread_utils
import time


TEST_INTERVAL = 0.1
SIZE = 10

SAMPLE_RESULTS = [0, 3, True, False, "FOO", "", None, object(), Exception()]
SAMPLE_EXCEPTIONS = [Exception(), RuntimeError("Foo")]


def test_create_worker_and_kill():
    """
    Pool(size) creates specified count of worker threads and kill() kills them.
    """

    # Wait for pre-tested threads are joined
    time.sleep(TEST_INTERVAL)

    initial_count = threading.active_count()
    p = thread_utils.Pool(SIZE)

    # Wait for all threads are generated.
    time.sleep(TEST_INTERVAL)

    assert threading.active_count() == initial_count + SIZE

    p.kill()

    # Wait for all threads are killed.
    time.sleep(TEST_INTERVAL)
    assert threading.active_count() == initial_count


class TestReceiveWhatTaskReturned(object):
    """
    What task returned can be accessible from Pool client.

    Pool.send method returns a future object and future.receive() returns
    what task returned.
    """

    def setup_method(self, method):
        self.p = thread_utils.Pool()

    def teardown_method(self, method):
        self.p.kill()

    def test_receive_what_task_function_returned(self):
        """
        future.receive() returns what task function returned.
        """

        def foo(val):
            return val

        futures = [self.p.send(foo, val) for val in SAMPLE_RESULTS]
        for sample, future in zip(SAMPLE_RESULTS, futures):
            assert sample is future.receive()

    def test_receive_what_task_method_returned(self):
        """
        future.receive() returns what task method returned.
        """

        class Foo(object):
            def foo(self, val):
                return val

        futures = [self.p.send(Foo().foo, val) for val in SAMPLE_RESULTS]
        for sample, future in zip(SAMPLE_RESULTS, futures):
            assert sample is future.receive()

    def test_receive_what_task_classmethod_returned(self):
        """
        future.receive() returns what task classmethod returned.
        """

        class Foo(object):
            @classmethod
            def foo(cls, val):
                return val

        futures = [self.p.send(Foo.foo, val) for val in SAMPLE_RESULTS]
        for sample, future in zip(SAMPLE_RESULTS, futures):
            assert sample is future.receive()

    def test_receive_what_task_staticmethod_returned(self):
        """
        future.receive() returns what task staticmethod returned.
        """

        class Foo(object):
            @staticmethod
            def foo(val):
                return val

        futures = [self.p.send(Foo.foo, val) for val in SAMPLE_RESULTS]
        for sample, future in zip(SAMPLE_RESULTS, futures):
            assert sample is future.receive()


class TestReceiveExceptionTaskRaised(object):
    """
    What task raised can is raised from Pool client.

    Pool.send method returns a future object and future.receive() raises
    Exception task raised
    """

    def setup_method(self, method):
        self.p = thread_utils.Pool()

    def teardown_method(self, method):
        self.p.kill()

    def test_receive_exception_task_function_raised(self):
        """
        future.receive() raises Exception task function raised.
        """

        def foo(e):
            raise e

        futures = [self.p.send(foo, e) for e in SAMPLE_EXCEPTIONS]
        for sample, future in zip(SAMPLE_EXCEPTIONS, futures):
            try:
                future.receive()
            except Exception as e:
                assert sample is e

    def test_receive_exception_task_method_raised(self):
        """
        future.receive() raises Exception task method raised.
        """

        class Foo(object):
            def bar(self, e):
                raise e

        futures = [self.p.send(Foo().bar, e) for e in SAMPLE_EXCEPTIONS]
        for sample, future in zip(SAMPLE_EXCEPTIONS, futures):
            try:
                future.receive()
            except Exception as e:
                assert sample is e

    def test_receive_exception_task_classmethod_raised(self):
        """
        future.receive() raises Exception task classmethod raised.
        """

        class Foo(object):
            @classmethod
            def bar(cls, e):
                raise e

        futures = [self.p.send(Foo.bar, e) for e in SAMPLE_EXCEPTIONS]
        for sample, future in zip(SAMPLE_EXCEPTIONS, futures):
            try:
                future.receive()
            except Exception as e:
                assert sample is e

    def test_receive_exception_task_staticmethod_raised(self):
        """
        future.receive() raises Exception task staticmethod raised.
        """

        class Foo(object):
            @staticmethod
            def bar(e):
                raise e

        futures = [self.p.send(Foo.bar, e) for e in SAMPLE_EXCEPTIONS]
        for sample, future in zip(SAMPLE_EXCEPTIONS, futures):
            try:
                future.receive()
            except Exception as e:
                assert sample is e


def test_worker_thread_will_be_used_specified_times():
    """
    Worker thread do taskes specified times, create a new worker
    and kill itself.
    """

    def foo():
        return threading.current_thread()

    p = thread_utils.Pool(worker_size=1, loop_count=2)
    futures = [p.send(foo) for i in xrange(3)]
    assert futures[0].receive() == futures[1].receive()
    assert futures[0].receive() != futures[2].receive()


def test_receive_raises_TimeoutError_if_task_do_not_finish_before_timeout():
    """
    future.receive() raises TimeoutError if task won't finish before timeout.
    """

    def foo(e):
        e.wait()

    p = thread_utils.Pool()

    event = threading.Event()
    event.clear()

    with pytest.raises(thread_utils.TimeoutError):
        p.send(foo, event).receive(timeout=TEST_INTERVAL)

    p.kill()


def test_DeadPoolError_if_task_is_sent_to_killed_Pool():
    """
    DeadPoolError is raised if task is sent to a Pool object which is killed.
    """

    def foo():
        pass

    p = thread_utils.Pool()
    p.kill()

    with pytest.raises(thread_utils.DeadPoolError):
        p.send(foo)


def test_can_be_used_with_statement_and_killed_when_exited():
    """
    Pool class can be used in with statement.

    Pool object is created when entered with statement and passed to variable
    specified as statement. The Pool object will be killed when exite from
    with statement.
    """

    # Wait for pre-tested threads are joined
    time.sleep(TEST_INTERVAL)

    initial_count = threading.active_count()

    with pytest.raises(RuntimeError):
        with thread_utils.Pool() as p:
            assert isinstance(p, thread_utils.Pool)
            raise RuntimeError()

    # Wait for all threads are killed.
    time.sleep(TEST_INTERVAL)

    assert threading.active_count() == initial_count
