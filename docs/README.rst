.. -*- coding: utf-8 -*-

==============
 thread_utils
==============

thread_utils is a utilities for thread program.

Requirements
============

* Python 2.7
* Unix or Linux platforms which support python thread module.

Tested
======

* Ubuntu 12.04 (x86_64)
* Mac OS X 10.9

Setup
=====

* Install from pip
  ::

     $ sudo pip install thread_utils

* Install from git.
  ::

    $ git clone https://github.com/wbcchsyn/python-thread_utils.git
    $ cd python-thread_utils
    $ sudo python setup.py install

Usage
=====
This module defines the following functions and class.

  thread_utils.async(daemon=True)

    Decorator that creates a worker thread and invokes callable there.

    Decorated callable object returns a Future object immediately and invoked
    callable starts to run in worker thread. If argument \`daemon\' is True,
    the worker thread will be daemonic; otherwise not. Python program exits
    when only daemon threads are left.

    In the following example, function sleep_sort print positive numbers in
    asending order. The main thread will terminate soon, however workers
    display numbers after that.
    ::

       """
       Print numbers in asending order using non daemonic workers.
       The main thread will terminate soon and after that workers do each task.
       """

       import thread_utils
       import time

       @thread_utils.async(daemon=False)
       def _sleep_print(n):
           time.sleep(n)
           print n

       def sleep_sort(un_sorted_list):
           """
           Print positive numbers in asending order.
           """

           for i in un_sorted_list:
               _sleep_print(i)

       sleep_sort([3,1,4,2]) # Numbers are displayed in asending this order.


    The decorated callable returns a Future object immediately; it monitors
    invoked callable progress and stores the result. The foreground thread can
    access to the result of invoked callable through the future object like as
    follows.
    ::

       import thread_utils
       import time

       @thread_utils.async(daemon=True)
       def add(m, n):
           time.sleep(m)
           return m + n

       future = add(3, 5)
       print "Task started"
       print future.receive() # Blocks for 3 seconds and display "8".

    See `Future Objects`_ for more information abaout it.

    This function decorates only function and method. In case of classmethod or
    staticmethod, decorating with this method before make classmethod or
    staticmethod.
    ::

       import thread_utils
       
       class Foo(object):
           @classmethod
           @thread_utils.async(daemon=False)
           def foo(cls):
               pass

    This decorator doesn't affect to thread safty, so it depends on the invoked
    callable whether decorated will be thread safe or not.

  thread_utils.Pool

    A class to pool worker threads and do tasks parallel using them. The worker
    threads are reused specified times for performance. The progress and the
    result of invoked callable can be seen through the Future object.

    See `Pool Objects`_ for more detail.

  thread_utils.synchronized

    Decorator to restrict from simultaneous access from 2 or more than 2
    threads.

    Decorated callable can be accessible from only one thread. If 2 or more
    than 2 threads try calling at the same time, only the 1st thread starts
    to run and the others are blocked. It is after the 1st thread finishes when
    2nd threads starts to run.
    ::

       import thread_utils
       import time

       @thread_utils.synchronized
       def foo():
           time.sleep(1)

       @thread_utils.async(daemon=False)
       def create_worker():
           print "Worker is started."
           foo()
           print "Worker is finished."

       
       # Text "Worker is started." will be printed 10 times at once.
       # On the other hand "Worker is finished." will be printed every second.
       for i in xrange(10):
           create_worker()

    This function decorates only functino or method. In case of classmethod or
    staticmethod, decorating with this method before make classmethod or
    staticmethod.
    ::

       class Foo(object):
           @staticmethod
           @thread_utils.synchronized
           def foo():
               pass

Future Objects
--------------

This class monitors associated callable progress and stores its return value or
unhandled exception. Future.is_finished() returns whether the invoked callable
is finished or not. Future.receive(timeout=None) blocks until timeout or
invoked callable is finished and returns what the callable returns or raises
its unhandled exception.

The instance will be created by thread_utils.Pool.send method or callable
decorated by thread_utils.async.

Future.is_finished()

  Return True if invoked callable is finished. Otherwise, return False.

Future.receive(timeout=None)

  Block until timeout or invoked callable is finished and returns what the
  callable returned or raises its unhandled exception.

  When argument \`timeout\' is presend and is not None, it shoule be int or
  floating number. This method raises TimeoutError if task won't be finished
  before timeout.

Pool Objects
------------

This class pools worker threads and do tasks parallel using them.

\`send\' method queues specified callable with the arguments and returns a
Future object immediately. The returned future object monitors the invoked
callable progress and stores the result.

The workers are reused for many times, so after using this object, \`kill\'
method must be called to join workers except for used in with statement.

class thread_utils.Pool(worker_size=1, loop_count=sys.maxint, daemon=True)

  All the arguments are optional. Argument \`worker_size\' specifies the number
  of the worker thread. The object can do this number of tasks at the same time
  parallel. Each worker will invoke callable \`loop_count\' times. After that,
  the worker kill itself and a new worker is created.

  If argument \`daemon\' is True, the worker thread will be daemonic, or not.
  Python program exits when only daemon threads are left.

  This constructor is thread safe.

  send(func, \*args, \*\*kwargs)

    Queue specified callable with the arguments and returns a Future object.

    Argument \`func \' is a callable object invoked by workers, and \*args and
    \*\*kwargs are arguments passed to it.

    The returned Future object monitors the progress of invoked callable and
    stores the result.

    See `Future Objects`_ for more detail abaout the return value.

    This method raises DeadPoolError if called after kill method is called.

    This method is thread safe.

  kill()

    Set internal flag and send terminate signal to all worker threads.

    This method returns immediately, however workers will work till the all
    queued callables are finished. After all callables are finished, workers
    kill themselves. If \`send\' is called after this method is called, it
    raises DeadPoolError.

    If this class is used in with statement, this method is called when the
    block exited. Otherwise, this method must be called after finished using
    the object.

    This method is thread safe and can be called many times.

  For example, the following program create pool with worker_size = 3. so
  display 3 messages every seconds. The Pool will be killed soon, but the
  worker do all tasks to be sent.
  ::

     import thread_utils
     import time

     def message(msg):
         time.sleep(1)
         return msg

     pool = thread_utils.Pool(worker_size=3)
     futures = []
     for i in xrange(7):
         futures.append(pool.send(message, "Message %d." % i))
     pool.kill()

     # First, sleep one second and "Message 0", "Message 1", "Message 2"
     # will be displayed.
     # After one second, Message 3 - 5 will be displayed.
     # Finally, "Message 6" will be displayed and program will exit.
     for f in futures:
         print f.receive()

  It is not necessary to call kill method if use with statement.
  ::
     
     import thread_utils
     import time

     def message(msg):
         time.sleep(1)
         return msg

     pool = thread_utils.Pool(worker_size=3)
     futures = []
     with thread_utils.Pool(worker_size=3) as pool:
         for i in xrange(7):
             futures.append(pool.send(message, "Message %d." % i))

     for f in futures:
         print f.receive()

Development
===========
Install requirements to developing and set pre-commit hook.
::

    $ git clone https://github.com/wbcchsyn/python-thread_utils.git
    $ cd python-thread_utils
    $ pip install -r dev_utils/requirements.txt
    $ ln -s ../../dev_utils/pre-commit .git/hooks/pre-commit
