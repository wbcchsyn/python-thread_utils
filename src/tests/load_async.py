#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import thread_utils


COUNT = 65535


@thread_utils.async()
def nothing():
    pass


if __name__ == '__main__':
    futures = [nothing() for i in xrange(COUNT)]
    for f in futures:
        f.receive()
