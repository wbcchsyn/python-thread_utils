#-*- coding: utf-8 -*-

import Queue
import threading
import operator
import sys

import _future
import _gc
import error


class Pool(object):

    class Task(object):
        __slots__ = ("future", "method", "args", "kwargs",)

        def __init__(self, future, method, *args, **kwargs):
            self.future = future
            self.method = method
            self.args = args
            self.kwargs = kwargs

    def __init__(self, worker_size=1, loop_count=sys.maxint, daemon=True):

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
        self.worker_size = worker_size
        self.loop_count = loop_count
        self.daemon = operator.truth(daemon)

        self.tasks = Queue.Queue()
        self.lock = threading.Lock()
        self.is_killed = False

        for i in xrange(worker_size):
            self.__create_worker()

    def __create_worker(self):
        t = threading.Thread(target=self.run)
        t.daemon = self.daemon
        t.start()

    def run(self):
        try:
            for i in xrange(self.loop_count):
                task = self.tasks.get()
                if task is None:
                    return

                try:
                    ret = task.method(*task.args, **task.kwargs)
                    task.future._set_return(ret)

                except BaseException as e:
                    task.future._set_error(e)

            else:
                self.__create_worker()

        finally:
            _gc.put(threading.current_thread())

    def send(self, method, *args, **kwargs):
        # Argument Check
        if not callable(method):
            raise TypeError("The argument 2 'method' is requested to be "
                            "callable.")

        future = _future.Future()
        task = self.Task(future, method, *args, **kwargs)
        with self.lock:
            if self.is_killed:
                raise error.DeadPoolError("Pool.send is called after killed.")
            self.tasks.put(task)

        return future

    def kill(self):
        with self.lock:
            self.is_killed = True

        [self.tasks.put(None) for i in xrange(self.worker_size)]

    def __del__(self):
        self.kill()
