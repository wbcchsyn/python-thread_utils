#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import thread_utils


SIZE = 64
COUNT = 1024


def nothing():
    pass


if __name__ == '__main__':
    futures = []
    with thread_utils.Pool(worker_size=SIZE) as pool:

        for i in xrange(COUNT):
            f = pool.send(nothing)
            for i in xrange(SIZE):
                futures.append(pool.send(nothing))
            f.receive()

    for f in futures:
        f.receive()
