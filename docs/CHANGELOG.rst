
CHANGELOG
=========

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
