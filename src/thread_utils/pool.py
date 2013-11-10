#-*- coding: utf-8 -*-

import Queue
import threading
import operator
import sys

import _future
import _gc
import error


class Pool(object):
    """
    Pool worker threads and do tasks parallel in background.

    'send' method will create a new task; the task is queued and will be done
    parallel in order.

    This class can be used in with statement and worker threads are killed
    when exit from with statement. Otherwise, programmer must call 'kill'
    method after finished to use this object.
    """

    class Task(object):
        __slots__ = ("future", "called", "args", "kwargs",)

        def __init__(self, future, called, *args, **kwargs):
            self.future = future
            self.called = called
            self.args = args
            self.kwargs = kwargs

    def __init__(self, worker_size=1, loop_count=sys.maxint, daemon=True):
        """
        All arguments are optional.

        Argument 'worker_size' specifies parallelism level. The object
        do this number tasks at the same time. It's default is 1.

        Argument 'loop_count' specifies how many tasks each worker do. Workers
        stop after done this count of task for garbage collection and create a
        new worker. This regeneration is done automatically so programer don't
        have to consider it.

        Argument 'daemon' specifies make workers daemonic or not. If it is True,
        workers stop when the main thread finished even though some tasks is
        left undone; otherwise workers carry on doing tasks untill all the
        tasks are done. The default value is True.
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
                    ret = task.called(*task.args, **task.kwargs)
                    task.future._set_return(ret)

                except BaseException as e:
                    task.future._set_error(e)

            else:
                self.__create_worker()

        finally:
            _gc.put(threading.current_thread())

    def send(self, called, *args, **kwargs):
        """
        Create a task, queue it and return the future object immediately.

        In the task, the argument 'called' is called; it should be function
        or method or classmethod or staticmethod. the optional arguments are
        passed to the called.

        For example, to call instance method foo.bar(1, a=2) as a task will be
        as follows.
        >>> p = Pool()
        >>> p.send(foo.bar, 1, a=2)

        The created task is done by worker sometime. Its progress and the result
        - either normal return valud or unhandled exception can be seen through
        the future object to be returned by this method.
        See help(thread_utils._future.Future) for information about what is
        returned by this method.

        This method is thread safe.
        """

        # Argument Check
        if not callable(called):
            raise TypeError("The argument 2 'called' is requested to be "
                            "callable.")

        future = _future.Future()
        task = self.Task(future, called, *args, **kwargs)
        with self.lock:
            if self.is_killed:
                raise error.DeadPoolError("Pool.send is called after killed.")
            self.tasks.put(task)

        return future

    def kill(self):
        """
        Set kill flag and stop to create a new task.

        After this method is called, method 'send' will raise DeadPoolError
        when called.

        This method won't block and return soon, however, tasks in queue will
        be done in order. Workers will kill itself after all the task is done.

        This method is thread safe.
        """

        with self.lock:
            self.is_killed = True

        [self.tasks.put(None) for i in xrange(self.worker_size)]

    def __del__(self):
        self.kill()

    def __enter__(self):
        return self

    def __exit__(self, error_type, value, traceback):
        self.kill()
