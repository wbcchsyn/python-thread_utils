# -*- coding: utf-8 -*-

import Queue
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

    __slots__ = ('__worker_size', '__loop_count', '__daemon', '__futures',
                 '__lock', '__is_killed',)

    def __init__(self, worker_size=1, loop_count=sys.maxint, daemon=True):
        """
        All arguments are optional.

        Argument `worker_size' specifies the number of the worker thread.
        The object can do this number of tasks at the same time parallel. Each
        worker will invoke callable `loop_count' times. After that, the worker
        kill itself and a new worker is created.

        If argument `daemon' is True, the worker thread will be daemonic, or
        not. Python program exits when only daemon threads are left.

        This constructor is thread safe.
        """

        # Argument Check
        if not isinstance(worker_size, int):
            raise TypeError("The argument 2 'worker_size' is requested "
                            "to be int.")
        if worker_size < 1:
            raise ValueError("The argument 2 'worker_size' is requested 1 or "
                             "larger than 1.")

        if not isinstance(loop_count, int):
            raise TypeError("The argument 3 'loop_count' is requested "
                            "to be int.")
        if loop_count < 1:
            raise ValueError("The argument 3 'loop_count' is requested to be 1"
                             " or larger than 1.")

        # main
        self.__worker_size = worker_size
        self.__loop_count = loop_count
        self.__daemon = operator.truth(daemon)

        self.__futures = Queue.Queue()
        self.__lock = threading.Lock()
        self.__is_killed = False

        for i in xrange(worker_size):
            self.__create_worker()

    def __create_worker(self):
        t = threading.Thread(target=self.__run)
        t.daemon = self.__daemon
        t.start()

    def __run(self):
        try:
            for i in xrange(self.__loop_count):
                future = self.__futures.get()
                if future is None:
                    return
                future._run()

            else:
                self.__create_worker()

        finally:
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

        future = _future.Future._create(func, *args, **kwargs)
        with self.__lock:
            if self.__is_killed:
                raise error.DeadPoolError("Pool.send is called after killed.")
            self.__futures.put(future)

        return future

    def kill(self):
        """
        Set internal flag and send terminate signal to all worker threads.

        This method returns immediately, however workers will work till the all
        queued callable are finished. After all callables are finished, workers
        kill themselves. If `send' is called after this methos is called, it
        raises DeadPoolError.

        If this class is used in with statement, this method is called when the
        block exited. Otherwise, this method must be called after finished
        using the object.

        This method is thread safe and can be callable many times.
        """

        with self.__lock:
            if self.__is_killed:
                return
            self.__is_killed = True

        [self.__futures.put(None) for i in xrange(self.__worker_size)]

    def __del__(self):
        self.kill()

    def __enter__(self):
        return self

    def __exit__(self, error_type, value, traceback):
        self.kill()
