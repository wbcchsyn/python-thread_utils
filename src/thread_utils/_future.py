#-*- coding: utf-8 -*-

import threading

import error


class Future(object):
    """
    Container to store what task returned and what task raised.
    """

    __slots__ = ('ret', 'error', '__is_finished',)

    def __init__(self):
        self.__is_finished = threading.Event()

    def _set_return(self, ret):

        self.ret = ret
        self.error = None
        self.__is_finished.set()

    def _set_error(self, error):

        self.ret = None
        self.error = error
        self.__is_finished.set()

    def is_finished(self):
        """
        Return True if the task is working, otherwise return False.
        """

        return self.__is_finished.is_set()

    def receive(self, timeout=None):
        """
        Wait until the task finished if necessary and return its result.

        This blocks until the task is finished and returns what the task
        returned when finished normally or raises unhandled exception in task
        unless timeout occurs.

        When the argument 'timeout' is present and not None, it should
        be int or floating number; this method raises TimeoutError if task is
        not finished before timeout.
        """

        # Argument Check
        t = type(timeout)
        if (timeout is not None) and (t is not int) and (t is not float):
            raise TypeError("The argument 2 'timeout' is requested "
                            "to be None, or int, or float.")

        self.__is_finished.wait(timeout)

        if not self.is_finished():
            raise error.TimeoutError

        if self.error is not None:
            raise self.error
        else:
            return self.ret
