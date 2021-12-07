#!/usr/bin/python3
"""Unit test for univention.config_registry.backend."""
# pylint: disable-msg=C0103,E0611,R0904
from threading import Thread, Lock

import pytest

from univention.config_registry.backend import ConfigRegistry  # noqa E402


class DummyLock(object):

	def __enter__(self):
		pass

	def __exit__(self, exc_type, exc_value, traceback):
		pass


@pytest.mark.slow
class TestConfigRegistry(object):

	"""Unit test for univention.config_registry.backend.ConfigRegistry"""

	def test_threading(self):
		"""Multiple threads accessing same registry."""
		DO_LOCKING = True
		THREADS = 10
		ITERATIONS = 1000
		BASE, PRIME = 7, 23
		KEY = 'x' * PRIME

		SKEY, SVALUE = 'always', 'there'
		ucr = ConfigRegistry()
		ucr[SKEY] = SVALUE
		ucr.save()

		lock = Lock() if DO_LOCKING else DummyLock()

		def run(tid):
			for iteration in range(ITERATIONS):
				i = tid + iteration
				random = pow(BASE, i, PRIME)
				key = KEY[:random + 1]

				with lock:
					ucr.load()
				assert ucr[SKEY] == SVALUE, 'tid=%d iter=%d %r' % (tid, iteration, ucr.items())

				try:
					del ucr[key]
				except LookupError:
					ucr[key] = '%d %d' % (tid, iteration)
				if i % 10 == 0 and tid % 10 == 0:
					with lock:
						ucr.save()

		threads = []
		for tid in range(THREADS):
			thread = Thread(target=run, name='%d' % tid, args=(tid,))
			threads.append(thread)
		for thread in threads:
			thread.start()
		for thread in threads:
			thread.join()
