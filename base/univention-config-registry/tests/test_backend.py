#!/usr/bin/python
"""Unit test for univention.config_registry.backend."""
# pylint: disable-msg=C0103,E0611,R0904
import unittest
import os
import sys
import tempfile
import shutil
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.path.pardir, 'python'))
from univention.config_registry.backend import ConfigRegistry


class TestConfigRegistry(unittest.TestCase):

	"""Unit test for univention.config_registry.backend.ConfigRegistry"""

	def setUp(self):
		"""Create object."""
		self.work_dir = tempfile.mkdtemp()
		ConfigRegistry.PREFIX = self.work_dir

	def tearDown(self):
		"""Destroy object."""
		shutil.rmtree(self.work_dir)

	def test_normal(self):
		"""Create NORMAL registry."""
		_ucr = ConfigRegistry()

		fname = os.path.join(self.work_dir, ConfigRegistry.BASES[ConfigRegistry.NORMAL])
		self.assertTrue(os.path.exists(fname))

	def test_ldap(self):
		"""Create LDAP registry."""
		_ucr = ConfigRegistry(write_registry=ConfigRegistry.LDAP)

		fname = os.path.join(self.work_dir, ConfigRegistry.BASES[ConfigRegistry.LDAP])
		self.assertTrue(os.path.exists(fname))

	def test_schedule(self):
		"""Create SCHEDULE registry."""
		_ucr = ConfigRegistry(write_registry=ConfigRegistry.SCHEDULE)

		fname = os.path.join(self.work_dir, ConfigRegistry.BASES[ConfigRegistry.SCHEDULE])
		self.assertTrue(os.path.exists(fname))

	def test_forced(self):
		"""Create FORCED registry."""
		_ucr = ConfigRegistry(write_registry=ConfigRegistry.FORCED)

		fname = os.path.join(self.work_dir, ConfigRegistry.BASES[ConfigRegistry.FORCED])
		self.assertTrue(os.path.exists(fname))

	def test_custom(self):
		"""Create CUSTOM registry."""
		fname = os.path.join(self.work_dir, 'custom.conf')

		_ucr = ConfigRegistry(fname)

		self.assertTrue(os.path.exists(fname))

	def test_custom_through_env(self):
		"""Create CUSTOM registry through environment variable."""
		fname = os.path.join(self.work_dir, 'custom.conf')
		os.environ['UNIVENTION_BASECONF'] = fname
		try:
			_ucr = ConfigRegistry(fname)

			self.assertTrue(os.path.exists(fname))
		finally:
			del os.environ['UNIVENTION_BASECONF']

	def test_save_load(self):
		"""Save and re-load UCR."""
		ucr = ConfigRegistry()
		ucr['foo'] = 'bar'
		ucr.save()

		ucr = ConfigRegistry()
		ucr.load()
		self.assertEqual(ucr['foo'], 'bar')

	def test_unset_getitem(self):
		"""Test unset ucr[key]."""
		ucr = ConfigRegistry()
		self.assertEqual(ucr['foo'], None)

	def test_getitem(self):
		"""Test set ucr[key]."""
		ucr = ConfigRegistry()
		ucr['foo'] = 'bar'
		self.assertEqual(ucr['foo'], 'bar')

	def test_empty_getitem(self):
		"""Test empty ucr[key]."""
		ucr = ConfigRegistry()
		ucr['foo'] = ''
		self.assertEqual(ucr['foo'], '')

	def test_unset_get(self):
		"""Test unset ucr[key]."""
		ucr = ConfigRegistry()
		self.assertEqual(ucr.get('foo'), None)

	def test_get(self):
		"""Test set ucr.get(key)."""
		ucr = ConfigRegistry()
		ucr['foo'] = 'bar'
		self.assertEqual(ucr.get('foo'), 'bar')

	def test_empty_get(self):
		"""Test empty ucr.get(key)."""
		ucr = ConfigRegistry()
		ucr['foo'] = ''
		self.assertEqual(ucr.get('foo'), '')

	def test_default_get(self):
		"""Test ucr.get(key, default)."""
		ucr = ConfigRegistry()
		self.assertEqual(ucr.get('foo', self), self)

	def test_scope_get_normal(self):
		"""Test NORMAL ucr.get(key, default)."""
		ucr = ConfigRegistry()
		ucr['foo'] = 'bar'
		self.assertEqual(ucr.get('foo', getscope=True), (ConfigRegistry.NORMAL, 'bar'))

	def test_scope_get_ldap(self):
		"""Test LDAP ucr.get(key, default)."""
		ucr = ConfigRegistry(write_registry=ConfigRegistry.LDAP)
		ucr['foo'] = 'bar'
		self.assertEqual(ucr.get('foo', getscope=True), (ConfigRegistry.LDAP, 'bar'))

	def test_scope_get_schedule(self):
		"""Test SCHEDULE ucr.get(key, default)."""
		ucr = ConfigRegistry(write_registry=ConfigRegistry.SCHEDULE)
		ucr['foo'] = 'bar'
		self.assertEqual(ucr.get('foo', getscope=True), (ConfigRegistry.SCHEDULE, 'bar'))

	def test_scope_get_forced(self):
		"""Test FORCED ucr.get(key, default)."""
		ucr = ConfigRegistry(write_registry=ConfigRegistry.FORCED)
		ucr['foo'] = 'bar'
		self.assertEqual(ucr.get('foo', getscope=True), (ConfigRegistry.FORCED, 'bar'))

	def test_has_key_unset(self):
		"""Test unset ucr.has_key(key)."""
		ucr = ConfigRegistry()
		self.assertFalse(ucr.has_key('foo'))

	def test_has_key_set(self):
		"""Test set ucr.has_key(key)."""
		ucr = ConfigRegistry()
		ucr['foo'] = 'bar'
		self.assertTrue(ucr.has_key('foo'))

	def test_has_key_write_unset(self):
		"""Test unset ucr.has_key(key, True)."""
		ucr = ConfigRegistry(write_registry=ConfigRegistry.FORCED)
		ucr['foo'] = 'bar'
		ucr = ConfigRegistry()
		self.assertFalse(ucr.has_key('foo', write_registry_only=True))

	def test_has_key_write_set(self):
		"""Test set ucr.has_key(key, True)."""
		ucr = ConfigRegistry(write_registry=ConfigRegistry.FORCED)
		ucr = ConfigRegistry()
		ucr['foo'] = 'bar'
		self.assertTrue(ucr.has_key('foo', write_registry_only=True))

	def test_pop(self):
		"""Test set ucr.pop(key)."""
		ucr = ConfigRegistry()
		ucr['foo'] = 'bar'
		self.assertEqual(ucr.pop('foo'), 'bar')

	def test_popitem(self):
		"""Test set ucr.popitem()."""
		ucr = ConfigRegistry()
		ucr['foo'] = 'bar'
		self.assertEqual(ucr.popitem(), ('foo', 'bar'))

	def test_setdefault(self):
		"""Test set ucr.setdefault()."""
		ucr = ConfigRegistry()
		ucr.setdefault('foo', 'bar')
		self.assertEqual(ucr['foo'], 'bar')

	@staticmethod
	def _setup_layers():
		ucr = ConfigRegistry(write_registry=ConfigRegistry.FORCED)
		ucr['foo'] = 'FORCED'
		ucr['bar'] = 'FORCED'
		ucr.save()
		ucr = ConfigRegistry()
		ucr['bar'] = 'NORMAL'
		ucr['baz'] = 'NORMAL'
		ucr.save()
		ucr = ConfigRegistry()
		ucr.load()
		return ucr

	def test_dict(self):
		"""Test merged items."""
		ucr = self._setup_layers()
		self.assertEqual(
			dict(ucr),
			dict([('foo', 'FORCED'), ('bar', 'FORCED'), ('baz', 'NORMAL')])
		)

	def test_items(self):
		"""Test merged items."""
		ucr = self._setup_layers()
		self.assertEqual(
			sorted(ucr.items()),
			sorted([('foo', 'FORCED'), ('bar', 'FORCED'), ('baz', 'NORMAL')])
		)

	def test_items_scopes(self):
		"""Test merged items."""
		ucr = self._setup_layers()
		self.assertEqual(
			sorted(ucr.items(getscope=True)),
			sorted([('foo', (ConfigRegistry.FORCED, 'FORCED')), ('bar', (ConfigRegistry.FORCED, 'FORCED')), ('baz', (ConfigRegistry.NORMAL, 'NORMAL'))])
		)

	@unittest.skipIf(sys.version_info >= (3,), "removed in python3")
	def test_iteritems(self):
		"""Test merged items."""
		ucr = self._setup_layers()
		self.assertEqual(
			sorted(ucr.iteritems()),
			sorted([('foo', 'FORCED'), ('bar', 'FORCED'), ('baz', 'NORMAL')])
		)

	def test_keys(self):
		"""Test merged keys."""
		ucr = self._setup_layers()
		self.assertEqual(
			sorted(ucr.keys()),
			sorted(['foo', 'bar', 'baz'])
		)

	@unittest.skipIf(sys.version_info >= (3,), "removed in python3")
	def test_iterkeys(self):
		"""Test merged keys."""
		ucr = self._setup_layers()
		self.assertEqual(
			sorted(ucr.iterkeys()),
			sorted(['foo', 'bar', 'baz'])
		)

	def test_values(self):
		"""Test merged values."""
		ucr = self._setup_layers()
		self.assertEqual(
			sorted(ucr.values()),
			sorted(['FORCED', 'FORCED', 'NORMAL'])
		)

	@unittest.skipIf(sys.version_info >= (3,), "removed in python3")
	def test_itervalues(self):
		"""Test merged items."""
		ucr = self._setup_layers()
		self.assertEqual(
			sorted(ucr.itervalues()),
			sorted(['FORCED', 'FORCED', 'NORMAL'])
		)

	def test_clear(self):
		"""Test set ucr.clear()."""
		ucr = self._setup_layers()
		ucr.clear()
		self.assertEqual(ucr.get('foo', getscope=True), (ConfigRegistry.FORCED, 'FORCED'))
		self.assertEqual(ucr.get('bar', getscope=True), (ConfigRegistry.FORCED, 'FORCED'))
		self.assertIsNone(ucr.get('baz', getscope=True))

	def test_is_true_unset(self):
		"""Test unset is_true()."""
		ucr = ConfigRegistry()
		self.assertFalse(ucr.is_true('foo'))

	def test_is_true_default(self):
		"""Test is_true(default)."""
		ucr = ConfigRegistry()
		self.assertTrue(ucr.is_true('foo', True))
		self.assertFalse(ucr.is_true('foo', False))

	def test_is_true_valid(self):
		"""Test valid is_true()."""
		ucr = ConfigRegistry()
		for ucr['foo'] in ('YES', 'yes', 'Yes', 'true', '1', 'enable', 'enabled', 'on'):
			self.assertTrue(ucr.is_true('foo'), 'is_true(%(foo)r)' % ucr)

	def test_is_true_invalid(self):
		"""Test invalid is_true()."""
		ucr = ConfigRegistry()
		for ucr['foo'] in ('yes ', ' yes', ''):
			self.assertFalse(ucr.is_true('foo'), 'is_true(%(foo)r)' % ucr)

	def test_is_true_valid_direct(self):
		"""Test valid is_true(value)."""
		ucr = ConfigRegistry()
		for value in ('YES', 'Yes', 'yes', 'true', '1', 'enable', 'enabled', 'on'):
			self.assertTrue(ucr.is_true(value=value), 'is_true(v=%r)' % value)

	def test_is_true_invalid_direct(self):
		"""Test invalid is_true(value)."""
		ucr = ConfigRegistry()
		for value in ('yes ', ' yes', ''):
			self.assertFalse(ucr.is_true(value=value), 'is_true(v=%r)' % value)

	def test_is_false_unset(self):
		"""Test unset is_false()."""
		ucr = ConfigRegistry()
		self.assertFalse(ucr.is_false('foo'))

	def test_is_false_default(self):
		"""Test is_false(default)."""
		ucr = ConfigRegistry()
		self.assertTrue(ucr.is_false('foo', True))
		self.assertFalse(ucr.is_false('foo', False))

	def test_is_false_valid(self):
		"""Test valid is_false()."""
		ucr = ConfigRegistry()
		for ucr['foo'] in ('NO', 'no', 'No', 'false', '0', 'disable', 'disabled', 'off'):
			self.assertTrue(ucr.is_false('foo'), 'is_false(%(foo)r)' % ucr)

	def test_is_false_invalid(self):
		"""Test invalid is_false()."""
		ucr = ConfigRegistry()
		for ucr['foo'] in ('no ', ' no', ''):
			self.assertFalse(ucr.is_false('foo'), 'is_false(%(foo)r)' % ucr)

	def test_is_false_valid_direct(self):
		"""Test valid is_false(value)."""
		ucr = ConfigRegistry()
		for value in ('NO', 'No', 'no', 'false', '0', 'disable', 'disabled', 'off'):
			self.assertTrue(ucr.is_false(value=value), 'is_false(v=%r)' % value)

	def test_is_false_invalid_direct(self):
		"""Test valid is_false(value)."""
		ucr = ConfigRegistry()
		for value in ('no ', ' no', ''):
			self.assertFalse(ucr.is_false(value=value), 'is_false(v=%r)' % value)

	def test_update(self):
		"""Test update()."""
		ucr = ConfigRegistry()
		ucr['foo'] = 'foo'
		ucr['bar'] = 'bar'
		ucr.update({
			'foo': None,
			'bar': 'baz',
			'baz': 'bar',
		})
		self.assertEqual(ucr.get('foo'), None)
		self.assertEqual(ucr.get('bar'), 'baz')
		self.assertEqual(ucr.get('baz'), 'bar')


class TestConfigRegistry2(unittest.TestCase):

	"""Unit test for univention.config_registry.backend.ConfigRegistry
	But without start up and tear down methods."""

	def test_locking(self):
		"""Test inter-process-locking."""
		self.work_dir = tempfile.mkdtemp()
		ConfigRegistry.PREFIX = self.work_dir
		# Finish start up
		delay = 1.0
		ucr = ConfigRegistry()
		read_end, write_end = os.pipe()

		pid1 = os.fork()
		if not pid1:  # child 1
			os.close(read_end)
			ucr.lock()
			os.write(write_end, '1')
			time.sleep(delay)
			ucr.unlock()
			os._exit(0)

		pid2 = os.fork()
		if not pid2:  # child 2
			os.close(write_end)
			os.read(read_end, 1)
			ucr.lock()
			time.sleep(delay)
			ucr.unlock()
			os._exit(0)

		os.close(read_end)
		os.close(write_end)

		timeout = time.time() + delay * 3
		while time.time() < timeout:
			pid, status = os.waitpid(0, os.WNOHANG)
			if (pid, status) == (0, 0):
				time.sleep(0.1)
			elif pid == pid1:
				self.assertTrue(os.WIFEXITED(status))
				self.assertEqual(os.WEXITSTATUS(status), 0)
				pid1 = None
			elif pid == pid2:
				self.assertTrue(os.WIFEXITED(status))
				self.assertEqual(os.WEXITSTATUS(status), 0)
				self.assertEqual(pid1, None, 'child 2 exited before child 1')
				break
			else:
				self.fail('Unknown child status: %d, %x' % (pid, status))
		else:
			self.fail('Timeout')
		# tear down
		shutil.rmtree(self.work_dir)


if __name__ == '__main__':
	unittest.main()
