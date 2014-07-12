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
