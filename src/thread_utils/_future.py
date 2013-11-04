#-*- coding: utf-8 -*-

import threading
import error


class Future(object):

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

        return self.__is_finished.is_set()

    def receive(self, timeout=None):

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
