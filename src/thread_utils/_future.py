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

    __slots__ = ('__result', '__is_error', '__func', '__args', '__kwargs',
                 '__lock',)

    def __init__(self, func, *args, **kwargs):
        self.__lock = threading.Condition(threading.Lock())
        self.__func = func
        self.__args = args
        self.__kwargs = kwargs
        self.__is_error = None

    def _run(self):
        try:
            result = self.__func(*self.__args, **self.__kwargs)
            self._set_result(result, False)

        except BaseException as e:
            self._set_result(e, True)

    def _set_result(self, result, is_error):
        self.__lock.acquire()
        try:
            self.__is_error = is_error
            self.__result = result

        finally:
            self.__lock.notify_all()
            self.__lock.release()

    def is_finished(self):
        """
        Return True if invoked callable is finished. Otherwise, return False.
        """

        self.__lock.acquire()
        try:
            return self.__is_error is not None
        finally:
            self.__lock.release()

    def receive(self, timeout=None):
        """
        Block until timeout or invoked callable is finished and returns what
        the callable returned or raises its unhandled exception.

        If the future object is generated by thread_utils.Pool.send method,
        and if the Pool instance is killed forcedly before the invoked task is
        started, this method raises DeadPoolError.

        When argument \`timeout\' is presend and is not None, it shoule be int
        or floating number. This method raises TimeoutError if task won't be
        finished before timeout.
        """

        self.__lock.acquire()
        try:
            if self.__is_error is None:
                self.__lock.wait(timeout)

        except Exception:
            pass

        finally:
            self.__lock.release()

        if self.__is_error is None:
            raise error.TimeoutError

        elif self.__is_error:
            raise self.__result

        else:
            return self.__result
