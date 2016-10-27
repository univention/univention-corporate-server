#!/usr/bin/python
"""Unit test for univention.config_registry.backend."""
# pylint: disable-msg=C0103,E0611,R0904
import unittest
import os
import sys
from tempfile import mkdtemp
from shutil import rmtree
from threading import Thread, Lock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.path.pardir, 'python'))
from univention.config_registry.backend import ConfigRegistry


class DummyLock(object):

	def __enter__(self):
		pass

	def __exit__(self, exc_type, exc_value, traceback):
		pass


class TestConfigRegistry(unittest.TestCase):

	"""Unit test for univention.config_registry.backend.ConfigRegistry"""

	def setUp(self):
		"""Create object."""
		self.work_dir = mkdtemp()
		ConfigRegistry.PREFIX = self.work_dir

	def tearDown(self):
		"""Destroy object."""
		# os.kill(os.getpid(), 19)  # signal.SIGSTOP
		rmtree(self.work_dir)

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
			for iteration in xrange(ITERATIONS):
				i = tid + iteration
				random = pow(BASE, i, PRIME)
				key = KEY[:random + 1]

				with lock:
					ucr.load()
				self.assertEqual(ucr[SKEY], SVALUE, 'tid=%d iter=%d %r' % (tid, iteration, ucr.items()))

				try:
					del ucr[key]
				except LookupError:
					ucr[key] = '%d %d' % (tid, iteration)
				if i % 10 == 0 and tid % 10 == 0:
					with lock:
						ucr.save()

		threads = []
		for tid in xrange(THREADS):
			thread = Thread(target=run, name='%d' % tid, args=(tid,))
			threads.append(thread)
		for thread in threads:
			thread.start()
		for thread in threads:
			thread.join()


if __name__ == '__main__':
	unittest.main()
