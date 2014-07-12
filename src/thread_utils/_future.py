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


import threading

import error


class Future(object):
    """
    This class monitors associated callable progress and stores its return
    value or unhandled exception. Future.is_finished() returns whether the
    invoked callable is finished or not. Future.receive(timeout=None) blocks
    until timeout or invoked callable is finished and returns what the callable
    returns or raises its unhandled exception.

    The instance will be created by thread_utils.Pool.send method or callable
    decorated by thread_utils.async.
    """

    __slots__ = ('__result', '__is_error', '__is_finished', '__func', '__args',
                 '__kwargs')

    def __new__(cls, *args, **kwargs):
        raise error.Error("Use Future._create to build this class.")

    @classmethod
    def _create(cls, func, *args, **kwargs):
        obj = super(cls, cls).__new__(cls)
        obj.__init__(func, *args, **kwargs)
        return obj

    def __init__(self, func, *args, **kwargs):
        self.__is_finished = threading.Event()
        self.__is_finished.clear()
        self.__func = func
        self.__args = args
        self.__kwargs = kwargs

    def _run(self):
        try:
            self.__result = self.__func(*self.__args, **self.__kwargs)
            self.__is_error = False

        except BaseException as e:
            self.__result = e
            self.__is_error = True

        finally:
            self.__is_finished.set()

    def is_finished(self):
        """
        Return True if invoked callable is finished. Otherwise, return False.
        """

        return self.__is_finished.is_set()

    def receive(self, timeout=None):
        """
        Block until timeout or invoked callable is finished and returns what
        the callable returned or raises its unhandled exception.

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
