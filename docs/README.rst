thread_utils
============
thread_utils is a utilities for thread program.

Requirements
^^^^^^^^^^^^
* Python 2.7
* Unix or Linux platforms which support python thread module.

Tested
^^^^^^
* Ubuntu 12.04 (x86_64)
* Mac OS X 10.9

Setup
^^^^^
* Install from git.
  ::

    $ git clone https://github.com/wbcchsyn/python-thread_utils.git
    $ cd python-thread_utils
    $ sudo python setup.py install

Development
^^^^^^^^^^^
Install requirements to developing and set pre-commit hook.
::

    $ git clone https://github.com/wbcchsyn/python-thread_utils.git
    $ cd python-thread_utils
    $ pip install -r dev_utils/requirements.txt
    $ ln -s ../../dev_utils/pre-commit .git/hooks/pre-commit
