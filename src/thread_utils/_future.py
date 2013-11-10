#-*- coding: utf-8 -*-

import threading

import error


class Future(object):
    """
    Container to store what task returned and what task raised.
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
