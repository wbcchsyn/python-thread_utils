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


class TestCreateAndKill(object):

    def test_create_worker_size(self):
        """
        Pool creates specified count of worker threads and kill() stops them.
        """

        # Wait for pre-tested threads are joined
        time.sleep(TEST_INTERVAL)

        initial_count = threading.active_count()
        p = thread_utils.Pool(SIZE)
        assert threading.active_count() == initial_count + SIZE
        assert p.inspect() == (SIZE, 0, 0,)

        # Make sure all workers are joined
        p.kill(block=True)
        time.sleep(TEST_INTERVAL)
        assert threading.active_count() == initial_count

    def test_tasks_are_done_after_killed(self):
        """
        Pool workers will do all queued tasks before stop when killed.
        """

        p = thread_utils.Pool()

        futures = [p.send(time.sleep, TEST_INTERVAL) for i in range(SIZE)]
        p.kill()

        # Check no timeout error occurres.
        [f.receive(timeout=TEST_INTERVAL * 10) for f in futures]

    def test_workers_stop_before_all_task_done_when_force_kill(self):
        """
        Pool workers will stop even if some tasks are left when forcely killed.
        """

        p = thread_utils.Pool()
        futures = [p.send(time.sleep, TEST_INTERVAL) for i in range(SIZE)]
        p.kill(force=True)

        # skip the first future check because the result is not stable.
        del(futures[0])

        # Check CancelError is raised.
        for f in futures:
            with pytest.raises(thread_utils.CancelError):
                f.receive()

        # If worker_size is 0, all features raise CancelError
        p = thread_utils.Pool(worker_size=0)
        futures = [p.send(time.sleep, TEST_INTERVAL) for i in range(SIZE)]
        assert p.inspect() == (0, 0, SIZE,)
        p.kill(force=True)

        # Check CancelError is raised.
        for f in futures:
            with pytest.raises(thread_utils.CancelError):
                f.receive()

    def test_kill_blocks_until_workers_died(self):
        """
        Pool.kill blocks until all workers finish the task if argument block
        is True.
        """

        p = thread_utils.Pool()
        futures = [p.send(time.sleep, TEST_INTERVAL) for i in range(SIZE)]
        assert p.inspect()[2] > 0
        p.kill(block=True)
        assert p.inspect() == (0, 0, 0,)

        # Check all tasks are finished.
        for f in futures:
            assert f.is_finished()

    def test_kill_forcely_and_block(self):
        """
        Test both force and block arguments are True
        """

        p = thread_utils.Pool()
        futures = [p.send(time.sleep, TEST_INTERVAL) for i in range(SIZE)]

        # Make sure the worker starts.
        time.sleep(TEST_INTERVAL / 2)
        assert p.inspect() == (1, 1, SIZE - 1,)
        p.kill(force=True, block=True)

        # The first task is finished.
        assert futures[0].is_finished()
        del(futures[0])

        # There is no undone tasks.
        assert p.inspect() == (0, 0, 0)

        # Check CancelError is raised.
        for f in futures:
            with pytest.raises(thread_utils.CancelError):
                f.receive()

    def test_inspect(self):
        '''
        Test inspect returns the right answer.
        '''

        p = thread_utils.Pool(worker_size=0)

        for i in range(SIZE):
            assert p.inspect() == (0, 0, i)
            p.send(lambda: None)

        p.kill(force=True)
        p.inspect() == (0, 0, 0)

        p = thread_utils.Pool(worker_size=1)
        for i in range(SIZE):
            p.send(time.sleep, TEST_INTERVAL)

        time.sleep(TEST_INTERVAL / 2)
        assert p.inspect() == (1, 1, SIZE - 1)
        time.sleep(TEST_INTERVAL)
        assert p.inspect() == (1, 1, SIZE - 2)

        p.kill()
        assert p.inspect() == (1, 1, SIZE - 2)

    def test_second_kill_can_block_till_task_done(self):
        '''
        Pool.kill(block=True) always blocks till all tasks are done.
        '''

        p = thread_utils.Pool()
        for i in range(SIZE):
            p.send(time.sleep, TEST_INTERVAL)

        # kill(block=True) blocks till all task is done even 2nd time.
        p.kill()
        assert p.inspect()[2] > 0
        p.kill(block=True)
        assert p.inspect() == (0, 0, 0,)

    def test_second_kill_can_cancel_undone_tasks(self):
        '''
        Pool.kill(force=True) always cancel all undone tasks.
        '''

        p = thread_utils.Pool()
        for i in range(SIZE):
            p.send(time.sleep, TEST_INTERVAL)

        # kill(block=True) blocks till all task is done even 2nd time.
        p.kill()
        assert p.inspect()[2] > 0
        p.kill(force=True)
        assert p.inspect()[2] == 0

    def test_cancel(self):
        '''
        Pool.cancel() cancels all undone tasks.
        '''

        p = thread_utils.Pool(worker_size=0)
        for i in range(SIZE):
            p.send(lambda: None)
        assert p.inspect() == (0, 0, SIZE,)
        p.cancel()
        assert p.inspect() == (0, 0, 0,)

        # cancel method works many times.
        for i in range(SIZE):
            p.send(lambda: None)
        assert p.inspect() == (0, 0, SIZE,)
        p.cancel()
        assert p.inspect() == (0, 0, 0,)

        # Cancel method works even worker_size is not 0.
        p = thread_utils.Pool()
        for i in range(SIZE):
            p.send(time.sleep, TEST_INTERVAL)
        p.cancel()
        assert p.inspect()[2] == 0

    def test_set_worker_size(self):
        '''
        Worker size can be changed after created.
        '''

        p = thread_utils.Pool(worker_size=0)
        for i in range(SIZE):
            p.send(lambda: None)
        assert p.inspect() == (0, 0, SIZE)

        # The worker size can be changed.
        p.set_worker_size(1)
        assert p.inspect()[0] == 1

        # The worker size can be changed many times.
        p.set_worker_size(2)
        assert p.inspect()[0] == 2

        # Tasks are finished now that worker_size > 0
        p.kill(block=True)

        p = thread_utils.Pool(worker_size=0)
        assert p.inspect() == (0, 0, 0)
        p.set_worker_size(3)
        assert p.inspect() == (3, 0, 0)

        # worker_size can be reduced
        p.set_worker_size(0)
        assert p.inspect() == (0, 0, 0)

        for i in range(SIZE):
            p.send(lambda: None)
        p.inspect() == (0, 0, SIZE)

        # undone task is not reduced because no worker is.
        time.sleep(TEST_INTERVAL)
        p.inspect() == (0, 0, SIZE)

        p.kill(force=True)


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

    def test_receive_exception_task_canceled(self):
        '''
        future.receive() raises CancelError when it is canceled before done.
        '''

        futures = [self.p.send(time.sleep, TEST_INTERVAL) for i in range(SIZE)]

        # Make sure the first task starts
        time.sleep(TEST_INTERVAL)
        self.p.cancel()

        # The first task does not raise nothing.
        futures[0].receive()
        # The last tasks will raise CancelError.
        with pytest.raises(thread_utils.CancelError):
            futures[-1].receive()

        # Make sure all tasks are canceled or finished.
        for f in futures:
            try:
                f.receive()
            except thread_utils.CancelError:
                pass

        # Pool.send works well after canceled.
        futures = [self.p.send(time.sleep, TEST_INTERVAL) for i in range(SIZE)]

        # Make sure the first task starts
        time.sleep(TEST_INTERVAL)
        self.p.cancel()

        # The first task does not raise nothing.
        futures[0].receive()
        # The last tasks will raise CancelError.
        with pytest.raises(thread_utils.CancelError):
            futures[-1].receive()


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
