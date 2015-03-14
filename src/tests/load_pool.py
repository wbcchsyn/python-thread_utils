#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import thread_utils


SIZE = 10
COUNT = 65535


def nothing():
    pass


if __name__ == '__main__':
    pool = thread_utils.Pool(worker_size=SIZE, daemon=True)
    futures = [pool.send(nothing) for i in xrange(COUNT)]

    pool.kill(block=True)
    for f in futures:
        f.receive()
