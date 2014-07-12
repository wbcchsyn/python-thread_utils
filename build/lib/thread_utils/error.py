# -*- coding: utf-8 -*-


class Error(Exception):
    pass


class TimeoutError(Error):
    pass


class DeadPoolError(Error):
    pass
