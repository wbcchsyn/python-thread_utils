#!-*- coding: utf-8 -*-
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


import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import threading
import time

import thread_utils


TEST_INTERVAL = 0.1
TEST_COUNT = 5

SAMPLE_RESULTS = [0, 3, True, False, "FOO", "", None, object(), Exception()]
SAMPLE_EXCEPTIONS = [Exception(), RuntimeError("Foo")]


class TestReceiveWhatInvokedCallableReturned(object):
    """
    What invoked callable returned can be accessible from foreground.

    Decorated callable returns a Future object and its receive() method
    returns what invoked callable returned.
    """

    def test_receive_what_invoked_function_returned(self):
        """
        Future.receive() returns what invoked function returned.
        """

        @thread_utils.async()
        def foo(ret):
            return ret

        for ret in SAMPLE_RESULTS:
            assert ret is foo(ret).receive()

    def test_receive_what_invoked_method_returned(self):
        """
        Future.receive() returns what invoked method returned.
        """

        class Foo(object):

            @thread_utils.async()
            def bar(self, n):
                return n

        for ret in SAMPLE_RESULTS:
            assert ret is Foo().bar(ret).receive()

    def test_receive_what_invoked_classmethod_returned(self):
        """
        Future.receive() returns what invoked classmethod returned.
        """

        class Foo(object):

            @classmethod
            @thread_utils.async()
            def bar(cls, n):
                return n

        for ret in SAMPLE_RESULTS:
            assert ret is Foo.bar(ret).receive()
            assert ret is Foo().bar(ret).receive()

    def test_receive_what_invoked_staticmethod_returned(self):
        """
        Future.receive() returns what invoked staticmethod returned.
        """

        class Foo(object):

            @staticmethod
            @thread_utils.async()
            def bar(n):
                return n

        for ret in SAMPLE_RESULTS:
            assert ret is Foo.bar(ret).receive()
            assert ret is Foo().bar(ret).receive()


class TestReceiveWhatInvakedCallableRaised(object):
    """
    Unhandled exception raised by invoked callable is raised in foreground.

    Decorated callable returns a Future object and Future.receive() raises
    unhandled exception raised by invoked callable.
    """

    def test_receive_raises_what_invoked_function_raised(self):
        """
        Future.receive() raises what invoked function raised.
        """

        @thread_utils.async()
        def foo(e):
            raise e

        for exception in SAMPLE_EXCEPTIONS:
            try:
                foo(exception)
            except Exception as e:
                assert exception is e

    def test_receive_raises_what_invoked_method_raised(self):
        """
        Future.receive() raises what invoked method raised.
        """

        class Foo(object):
            @thread_utils.async()
            def bar(self, e):
                raise e

        for exception in SAMPLE_EXCEPTIONS:
            try:
                Foo().bar(exception)
            except Exception as e:
                assert exception is e

    def test_receive_raises_what_invoked_classfunction_raised(self):
        """
        Future.receive() raises what invoked classfunction raised.
        """

        class Foo(object):
            @classmethod
            @thread_utils.async()
            def bar(cls, e):
                raise e

        for exception in SAMPLE_EXCEPTIONS:
            try:
                Foo.bar(exception)
            except Exception as e:
                assert exception is e

    def test_receive_raises_what_invoked_staticmethod_raised(self):
        """
        future.receive() raises what invoked staticmethod raised.
        """

        class Foo(object):
            @staticmethod
            @thread_utils.async()
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

    @thread_utils.async()
    def foo():
        pass

    # Wait for threads of another test will be joined.
    time.sleep(TEST_INTERVAL)

    active_threads = threading.active_count()
    [foo() for i in range(TEST_COUNT)]

    # Wait for threads are joined.
    time.sleep(TEST_INTERVAL)
    assert threading.active_count() == active_threads


def test_worker_is_daemonic_unless_specified():
    """
    Worker thread is daemonic in default, but it can be specified.
    """

    def foo():
        return threading.current_thread().daemon

    default = thread_utils.async()(foo)
    daemonic = thread_utils.async(daemon=True)(foo)
    non_daemonic = thread_utils.async(daemon=False)(foo)

    assert default().receive()
    assert daemonic().receive()
    assert not non_daemonic().receive()


def test_receive_raises_TimeoutError_if_task_do_not_finish_before_timeout():
    """
    Future.receive() raises TimeoutError if task won't finish before timeout.
    """

    event = threading.Event()
    event.clear()

    @thread_utils.async()
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

    @thread_utils.async()
    def foo():
        event.wait()

    f = foo()

    time.sleep(TEST_INTERVAL)
    assert not f.is_finished()

    event.set()
    time.sleep(TEST_INTERVAL)
    assert f.is_finished()
