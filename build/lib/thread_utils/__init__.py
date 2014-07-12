# -*- coding: utf-8 -*-

import sys


# To support 2.x and 3.x, use __import__.
synchronized = __import__('synchronized', globals(), locals(),
                          ['synchronized'], 1).synchronized
async = __import__('async', globals(), locals(), ['async'], 1).async
__errors = __import__('error', globals(), locals(), [], 1)
Error = __errors.Error
TimeoutError = __errors.TimeoutError
DeadPoolError = __errors.DeadPoolError
Pool = __import__('pool', globals(), locals(), ['Pool'], 1).Pool
Future = __import__('_future', globals(), locals(), ['Future'], 1).Future
