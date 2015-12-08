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


import collections
import threading
import operator
import sys

import _future
import _gc
import error


class Pool(object):
    """
    Pool worker threads and do tasks parallel using them.

    `send' method queues specified callable with the arguments and returns a
    Future object immediately. The returned future object monitors the invoked
    callable progress and stores the result.

    The workers are reused for many times, so after using this object, kill
    method must be called to join workers except for used in with statement.

    All public methods are thread safe.
    """

    __slots__ = (
        '__worker_size',  # How many workers should be.
        '__workers',  # dict of workers. { thread_id: doing_task_or_not }
        '__daemon',  # Workers are daemon thread or not.
        '__loop_count',  # How many tasks each worker does before regenerate.
        '__futures',  # Futures of undone tasks and stop signals.
        '__lock',  # exclusive lock (Condition).
        '__is_killed',  # whether pool is killed or not.
        '__stop_signals',  # How many stop signals are queued.
    )

    def __init__(self, worker_size=1, loop_count=sys.maxint, daemon=True):
        """
        All arguments are optional.

        Argument `worker_size' specifies the number of the worker thread.
        The object can do this number of tasks at the same time parallel. Each
        worker will invoke callable `loop_count' times. After that, the worker
        kill itself and a new worker is created.

        If argument `daemon' is True, the worker threads will be daemonic, or
        not. Python program exits when only daemon threads are left.
        """

        # Argument Check
        if not isinstance(worker_size, int):
            raise TypeError("The argument 2 'worker_size' is requested "
                            "to be int.")
        if worker_size < 0:
            raise ValueError("The argument 2 'worker_size' is requested 0 or "
                             "larger than 0.")

        if not isinstance(loop_count, int):
            raise TypeError("The argument 3 'loop_count' is requested "
                            "to be int.")
        if loop_count < 1:
            raise ValueError("The argument 3 'loop_count' is requested to be 1"
                             " or larger than 1.")

        # Immutable variables
        self.__daemon = operator.truth(daemon)
        self.__loop_count = loop_count

        # Lock
        self.__lock = threading.Condition(threading.Lock())

        # Mutable variables
        self.__is_killed = False
        self.__worker_size = worker_size
        self.__futures = collections.deque()
        self.__stop_signals = 0
        self.__workers = {}

        for i in xrange(worker_size):
            self.__create_worker()

    def __create_worker(self):
        t = threading.Thread(target=self.__run)
        t.daemon = self.__daemon
        t.start()

    def __run(self):

        # Add own thread object to self.__workers
        my_id = id(threading.current_thread())
        with self.__lock:
            self.__workers[my_id] = False

        # Helper Function
        def worker_exit_at():
            with self.__lock:
                # Delete own thread object.
                del(self.__workers[my_id])

                # Decrease worker_size when pool is being killed.
                if self.__is_killed:
                    self.__worker_size = len(self.__workers)
                    # Wake up all kill methods when the last worker is killed.
                    if self.__worker_size == 0:
                        self.__lock.notify_all()

            _gc._put(threading.current_thread())

        # Method routine start
        try:
            loop_count = 0
            while loop_count < self.__loop_count:
                try:
                    # dequeu.popleft() is thread safe.
                    future = self.__futures.popleft()

                    if future is None:
                        # kill itself if the task is None (stop signal).
                        with self.__lock:
                            self.__stop_signals -= 1
                        return

                    loop_count += 1
                    self.__workers[my_id] = True
                    future._run()
                    self.__workers[my_id] = False

                except IndexError:
                    # If self.__futures is empty, wait until task comes.
                    with self.__lock:
                        while not self.__futures:
                            self.__lock.wait()

            # Recreate a worker before suiside when loop ends.
            self.__create_worker()

        finally:
            worker_exit_at()

    def send(self, func, *args, **kwargs):
        """
        Queue specified callable with the arguments and returns a Future
        object.

        Argument `func' is a callable object invoked by workers, and *args
        and **kwargs are arguments passed to it.

        The returned Future object monitors the progress of invoked callable
        and stores the result. The result can be accessed through the Future
        instance.

          import thread_utils
          import time

          def message(msg):
              time.sleep(1)
              return msg

          pool = thread_utils.Pool(worker_size=3)
          futures = []
          with thread_utils.Pool(worker_size=3) as pool:
              for i in xrange(7):
                  futures.append(pool.send(message, "Message %d." % i))

          # First, sleep one second and "Message 0", "Message 1", "Message 2"
          # will be displayed.
          # After one second, Message 3 - 5 will be displayed.
          # Finally, "Message 6" will be displayed and program will exit.
          for f in futures:
              print f.receive()

        See help(thread_utils.Future) for more detail abaout the return value.

        This method raises DeadPoolError if called after kill method is called.
        """

        # Argument Check
        if not callable(func):
            raise TypeError("The argument 2 'func' is requested to be "
                            "callable.")

        with self.__lock:
            if self.__is_killed:
                raise error.DeadPoolError("Pool.send is called after killed.")

            # Wake up workers waiting task.
            if not self.__futures:
                self.__lock.notify()

            future = _future.PoolFuture(func, *args, **kwargs)
            self.__futures.append(future)
            return future

    def kill(self, force=False, block=False):
        """
        Set internal flag and make workers stop.

        If the argument force is True, all queued tasks are canceled; the
        workers will stop after their current task is finished. In this case,
        tasks not started before this method is called will be left undone.
        If a Future instance is related to canceled task and the receive
        method is called, it will raise CancelError. The default value is
        False.

        If the argument block is True, block until the all workers done the
        tasks. Otherwise, it returns immediately. The default value is False.
        If this method is called in a task with argument block is True, dead
        lock will occur.

        If `send' or `set_worker_size' is called after this methos is called,
        it raises DeadPoolError.

        This method can be called many times.
        If argument force is True, cancel undone tasks then. If argument block
        is True, it blocks until all workers done tasks.

        If this class is used in with statement, this method is called with
        default arguments when the block exited. Otherwise, this method must
        be called after finished using the object, or the worker threads are
        left till the program ends.
        (Or, if the constructor is called with optional argument daemon=False,
        dead lock occurres and program will never ends.)
        """

        with self.__lock:
            self.__is_killed = True

            if force:
                self.cancel()

            for i in xrange(self.__worker_size):
                self.__futures.append(None)
            self.__stop_signals += self.__worker_size
            # Wake up workers waitin task or stop signal.
            self.__lock.notify_all()

            if block:
                while self.__worker_size > 0:
                    self.__lock.wait()

    def inspect(self):
        '''
        Return tuple which indicate the instance status.

        The return value is a tuple of 3 ints. The format is as follows.
        (worker size, tasks currently being done, queued undone tasks)

        The values are only indication.
        Even the instance itself doesn't know the accurate values.
        '''

        tasks_being_done = sum(self.__workers.itervalues())
        queued_tasks = len(self.__futures) - self.__stop_signals
        return (self.__worker_size, tasks_being_done, queued_tasks,)

    def cancel(self):
        '''
        Cancel all tasks in the Queue.

        Cancel all tasks before started. This method can be called whenever,
        even after the pool is killed.

        Tasks are dequeued when it is started to do. Tasks being done are left
        unchanged. So this method can be called from task. (Of course, it can
        be called from outside of the task, too.)

        If a future is related to canceled task and the receive method is
        called, it will raise CancelError.
        '''

        # Store how many stop signals to fetch to append again.
        stop_signals = 0
        try:
            # Pop all futures.
            while True:
                # dequeue.pop() is thread safe.
                f = self.__futures.pop()

                if f is None:
                    stop_signals += 1

                else:
                    f._set_result(error.CancelError("This task was canceled "
                                                    "before done."), True)
        except IndexError:
            # Append as many stop signals as poped.
            for i in xrange(stop_signals):
                self.__futures.appendleft(None)

    def set_worker_size(self, worker_size):
        '''
        Change worker size.

        This method set the worker size and return soon. The workers will
        created soon when increasing,howeve, It could take some time when
        decreasing because workers can't stop while doing a task.

        This method raises DeadPoolError if called after kill method is called.
        '''

        with self.__lock:
            if self.__is_killed:
                raise error.DeadPoolError("Pool.set_worker_size is called "
                                          "after killed.")

            while self.__worker_size < worker_size:
                self.__create_worker()
                self.__worker_size += 1

            while worker_size < self.__worker_size:
                self.__futures.appendleft(None)
                self.__stop_signals += 1
                self.__worker_size -= 1

            # Wake up workers waiting for task or stop signal.
            self.__lock.notify_all()

    def __del__(self):
        self.kill()

    def __enter__(self):
        return self

    def __exit__(self, error_type, value, traceback):
        self.kill()
