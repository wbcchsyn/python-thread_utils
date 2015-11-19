# -*- coding: utf-8 -*-
'''
Copyright 2014 Yoshida Shin

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
    """

    __slots__ = ('__worker_size', '__daemon', '__futures', '__lock',
                 '__is_killed', '__queue_size', '__workings',
                 '__current_workers')

    def __init__(self, worker_size=1, daemon=True):
        """
        All arguments are optional.

        Argument `worker_size' specifies the number of the worker thread.
        The object can do this number of tasks at the same time parallel.

        If argument `daemon' is True, the worker thread will be daemonic, or
        not. Python program exits when only daemon threads are left.

        This constructor is thread safe.
        """

        # Argument Check
        if not isinstance(worker_size, int):
            raise TypeError("The argument 2 'worker_size' is requested "
                            "to be int.")
        if worker_size < 0:
            raise ValueError("The argument 2 'worker_size' is requested 0 or "
                             "larger than 0.")

        # Immutable variables
        self.__daemon = operator.truth(daemon)
        self.__worker_size = worker_size

        # Lock
        self.__lock = threading.Condition(threading.Lock())

        # Mutable variables
        self.__is_killed = False
        self.__current_workers = 0
        self.__futures = collections.deque()
        self.__queue_size = 0
        self.__workings = 0

        for i in xrange(worker_size):
            self.__create_worker()

    def __create_worker(self):
        t = threading.Thread(target=self.__run)
        t.daemon = self.__daemon
        t.start()
        self.__current_workers += 1

    def __run(self):
        try:
            while True:
                try:
                    self.__lock.acquire()
                    while self.__queue_size == 0 and not self.__is_killed:
                        self.__lock.wait()

                    if self.__queue_size == 0 and self.__is_killed:
                        return

                    future = self.__futures.popleft()
                    self.__queue_size -= 1

                    self.__workings += 1

                    # Release lock only when doing task.
                    self.__lock.release()
                    future._run()
                    self.__lock.acquire()

                    self.__workings -= 1

                finally:
                    self.__lock.release()

        finally:
            with self.__lock:
                self.__current_workers -= 1
                if self.__current_workers == 0:
                    self.__lock.notify_all()
            _gc._put(threading.current_thread())

    def send(self, func, *args, **kwargs):
        """
        Queue specified callable with the arguments and returns a Future
        object.

        Argument `func' is a callable object invoked by workers, and *args
        and **kwargs are passed to it.

        The returned Future object monitors the progress of invoked callable
        and stores the result.

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

        This method is thread safe.
        """

        # Argument Check
        if not callable(func):
            raise TypeError("The argument 2 'func' is requested to be "
                            "callable.")

        with self.__lock:
            if self.__is_killed:
                raise error.DeadPoolError("Pool.send is called after killed.")

            future = _future.PoolFuture(func, *args, **kwargs)
            self.__futures.append(future)
            self.__queue_size += 1
            self.__lock.notify()
            return future

    def kill(self, force=False, block=False):
        """
        Set internal flag and make workers stop.

        If the argument force is True, the workers will stop after their
        current task is finished. In this case, some futures could be left
        undone, and they will raise DeadPoolError when their receive method
        is called. On the other hand, if the argument force is False, the
        workers will stop after all queued tasks are finished. The default is
        value False.

        If the argument block is True, block until the all workers done the
        tasks. Otherwise, it returns immediately. The default value is False.

        If `send' is called after this methos is called, it raises
        DeadPoolError.

        If this class is used in with statement, this method is called when the
        block exited. Otherwise, this method must be called after finished
        using the object, or the worker threads are left till the program ends.
        (Or, if the constructor is called with optional argument daemon=False,
        dead lock occurres and program will never ends.)

        This method is thread safe and can be callable many times.
        """

        self.__lock.acquire()
        try:
            self.__is_killed = True
            self.__lock.notify_all()

            if force:
                for f in self.__futures:
                    f._set_result(
                        error.DeadPoolError("The pool is killed before the"
                                            " task is done."),
                        True
                    )

                self.__futures.clear()
                self.__queue_size = 0

            if block:
                while self.__current_workers > 0:
                    self.__lock.wait()

        finally:
            self.__lock.release()

    def inspect(self):
        '''
        Return tuple which indicate the instance status.

        The return value is a tuple of 3 ints. the format is as follows.
        (worker size, tasks currently being done, queued undone tasks)
        '''

        return (self.__worker_size, self.__workings, self.__queue_size,)

    def __del__(self):
        self.kill()

    def __enter__(self):
        return self

    def __exit__(self, error_type, value, traceback):
        self.kill()
