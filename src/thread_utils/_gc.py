# -*- coding: utf-8 -*-

import Queue
import threading


__TERMINATED = Queue.Queue()
__GC = None


def __gc():
    try:
        while True:
            __TERMINATED.get().join()
    except:
        # Daemon thread seldom raises error at exit in some conditions in
        # python 2.6.
        pass


def _put(thread):
    __TERMINATED.put(thread)


if __GC is None:
    __GC = threading.Thread(target=__gc)
    __GC.daemon = True
    __GC.name = "Garbage Collector."
    __GC.start()
