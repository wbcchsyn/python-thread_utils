
CHANGELOG
=========

1.0.0 (2015/12/08)
------------------

* Change the behavior when Pool.kill method called twice or more than twice.
* Add Pool.inspect and Pool.cancel method.
* Enable to change worker size of Pool instance after created.
* Performance tuning.
* Stop to support python2.6, 3.1 and 3.2.

0.1.3 (2015/03/15)
------------------

* Bug Fix: Pool.kill method could raise Queue.Empty error.
* Performance tuning.

0.1.2 (2014/09/14)
------------------

* Create actor alias to async decorator.
* Add optional arguments 'force' and 'block' to Pool.kill method.
* Future.receive method raise DeadPoolError if the Pool is killed before task
  is done.
* Update documents.

0.1.1 (2014/06/13)
------------------

* Delete unused files.

0.1.0 (2014/06/12)
------------------

* First release.
