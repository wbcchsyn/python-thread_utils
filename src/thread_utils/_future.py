#-*- coding: utf-8 -*-

import threading

import error


class Future(object):
    """
    This class monitors associated task and stores its return value or
    unhandled exception. Future.is_finished() returns whether the task is
    finished or not. Future.receive(timeout=None) blocks until timeout or task
    is finished and returns what callable invoked task returns or raises its
    unhandled exception.

    The instance will be created by thread_utils.Pool.send method or callable
    decorated by thread_utils.async.
    """

    __slots__ = ('__result', '__is_error', '__is_finished')

    def __init__(self):
        self.__is_finished = threading.Event()
        self.__is_finished.clear()

    def _run(self, func, *args, **kwargs):
        try:
            self.__result = func(*args, **kwargs)
            self.__is_error = False

        except BaseException as e:
            self.__result = e
            self.__is_error = True

        finally:
            self.__is_finished.set()

    def is_finished(self):
        """
        Return True if task is finished. Otherwise, return False.
        """

        return self.__is_finished.is_set()

    def receive(self, timeout=None):
        """
        Block until timeout or task is finished and returns what invoked
        callable returned or raises its unhandled exception.

        When argument \`timeout\' is presend and is not None, it shoule be int
        or floating number. This method raises TimeoutError if task won't be
        finished before timeout.
        """

        # Argument Check
        if (timeout is not None) and \
                (not isinstance(timeout, int)) and \
                (not isinstance(timeout, float)):
            raise TypeError("The argument 2 'timeout' is requested "
                            "to be None, or int, or float.")

        self.__is_finished.wait(timeout)

        if not self.is_finished():
            raise error.TimeoutError

        if self.__is_error:
            raise self.__result
        else:
            return self.__result
