#!/usr/bin/python
"""Unit test for univention.config_registry.backend."""
# pylint: disable-msg=C0103,E0611,R0904
import os
import sys
import six
import time
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.path.pardir, 'python'))
from univention.config_registry.backend import ConfigRegistry  # noqa E402

py2_only = pytest.mark.skipif(six.PY3, reason="Python 2 only")

TRUE_VALID = ('YES', 'yes', 'Yes', 'true', '1', 'enable', 'enabled', 'on')
TRUE_INVALID = ('yes ', ' yes', '')
FALSE_VALID = ('NO', 'no', 'No', 'false', '0', 'disable', 'disabled', 'off')
FALSE_INVALID = ('no ', ' no', '')


@pytest.fixture
def ucr0(tmpdir):
	ConfigRegistry.PREFIX = str(tmpdir)
	ucr = ConfigRegistry()
	return ucr


@pytest.fixture
def ucrf(ucr0):
	ucr = ConfigRegistry(write_registry=ConfigRegistry.FORCED)
	ucr['foo'] = 'FORCED'
	ucr['bar'] = 'FORCED'
	ucr.save()
	ucr = ConfigRegistry()
	ucr['bar'] = 'NORMAL'
	ucr['baz'] = 'NORMAL'
	ucr.save()
	ucr0.load()
	return ucr0


class TestConfigRegistry(object):

	"""Unit test for univention.config_registry.backend.ConfigRegistry"""

	def test_normal(self, ucr0, tmpdir):
		"""Create NORMAL registry."""
		assert (tmpdir / ConfigRegistry.BASES[ConfigRegistry.NORMAL]).exists()

	def test_ldap(self, ucr0, tmpdir):
		"""Create LDAP registry."""
		_ucr = ConfigRegistry(write_registry=ConfigRegistry.LDAP)  # noqa F841

		assert (tmpdir / ConfigRegistry.BASES[ConfigRegistry.LDAP]).exists()

	def test_schedule(self, ucr0, tmpdir):
		"""Create SCHEDULE registry."""
		_ucr = ConfigRegistry(write_registry=ConfigRegistry.SCHEDULE)  # noqa F841

		assert (tmpdir / ConfigRegistry.BASES[ConfigRegistry.SCHEDULE]).exists()

	def test_forced(self, ucr0, tmpdir):
		"""Create FORCED registry."""
		_ucr = ConfigRegistry(write_registry=ConfigRegistry.FORCED)  # noqa F841

		assert (tmpdir / ConfigRegistry.BASES[ConfigRegistry.FORCED]).exists()

	def test_custom(self, ucr0, tmpdir):
		"""Create CUSTOM registry."""
		fname = tmpdir / 'custom.conf'

		_ucr = ConfigRegistry(str(fname))  # noqa F841

		assert fname.exists()

	def test_custom_through_env(self, monkeypatch, tmpdir):
		"""Create CUSTOM registry through environment variable."""
		fname = tmpdir / 'custom.conf'
		monkeypatch.setenv('UNIVENTION_BASECONF', str(fname))

		_ucr = ConfigRegistry(str(fname))  # noqa F841

		assert fname.exists()

	def test_save_load(self, ucr0):
		"""Save and re-load UCR."""
		ucr0['foo'] = 'bar'
		ucr0.save()

		ucr = ConfigRegistry()
		ucr.load()
		assert ucr['foo'] == 'bar'

	def test_unset_getitem(self, ucr0):
		"""Test unset ucr[key]."""
		ucr = ConfigRegistry()
		assert ucr['foo'] is None

	def test_getitem(self, ucr0):
		"""Test set ucr[key]."""
		ucr0['foo'] = 'bar'
		assert ucr0['foo'] == 'bar'

	def test_empty_getitem(self, ucr0):
		"""Test empty ucr[key]."""
		ucr0['foo'] = ''
		assert ucr0['foo'] == ''

	def test_unset_get(self, ucr0):
		assert ucr0.get('foo') is None

	def test_get(self, ucr0):
		"""Test set ucr.get(key)."""
		ucr0['foo'] = 'bar'
		assert ucr0.get('foo') == 'bar'

	def test_empty_get(self, ucr0):
		"""Test empty ucr.get(key)."""
		ucr0['foo'] = ''
		assert ucr0.get('foo') == ''

	def test_default_get(self, ucr0):
		"""Test ucr.get(key, default)."""
		assert ucr0.get('foo', self) is self

	def test_scope_get_normal(self, ucr0):
		"""Test NORMAL ucr.get(key, default)."""
		ucr0['foo'] = 'bar'
		assert ucr0.get('foo', getscope=True) == (ConfigRegistry.NORMAL, 'bar')

	def test_scope_get_ldap(self, ucr0):
		"""Test LDAP ucr.get(key, default)."""
		ucr = ConfigRegistry(write_registry=ConfigRegistry.LDAP)
		ucr['foo'] = 'bar'
		assert ucr.get('foo', getscope=True) == (ConfigRegistry.LDAP, 'bar')

	def test_scope_get_schedule(self, ucr0):
		"""Test SCHEDULE ucr.get(key, default)."""
		ucr = ConfigRegistry(write_registry=ConfigRegistry.SCHEDULE)
		ucr['foo'] = 'bar'
		assert ucr.get('foo', getscope=True) == (ConfigRegistry.SCHEDULE, 'bar')

	def test_scope_get_forced(self, ucr0):
		"""Test FORCED ucr.get(key, default)."""
		ucr = ConfigRegistry(write_registry=ConfigRegistry.FORCED)
		ucr['foo'] = 'bar'
		assert ucr.get('foo', getscope=True) == (ConfigRegistry.FORCED, 'bar')

	def test_has_key_unset(self, ucr0):
		"""Test unset ucr.has_key(key)."""
		assert not ucr0.has_key('foo')  # noqa W601

	def test_has_key_set(self, ucr0):
		"""Test set ucr.has_key(key)."""
		ucr0['foo'] = 'bar'
		assert ucr0.has_key('foo')  # noqa W601

	def test_has_key_write_unset(self, ucr0):
		"""Test unset ucr.has_key(key, True)."""
		ucr = ConfigRegistry(write_registry=ConfigRegistry.FORCED)
		ucr['foo'] = 'bar'
		ucr = ConfigRegistry()
		assert not ucr.has_key('foo', write_registry_only=True)  # noqa W601

	def test_has_key_write_set(self, ucr0):
		"""Test set ucr.has_key(key, True)."""
		ucr = ConfigRegistry(write_registry=ConfigRegistry.FORCED)
		ucr = ConfigRegistry()
		ucr['foo'] = 'bar'
		assert ucr.has_key('foo', write_registry_only=True)  # noqa W601

	def test_pop(self, ucr0):
		"""Test set ucr.pop(key)."""
		ucr0['foo'] = 'bar'
		assert ucr0.pop('foo') == 'bar'

	def test_popitem(self, ucr0):
		"""Test set ucr.popitem()."""
		ucr0['foo'] = 'bar'
		assert ucr0.popitem() == ('foo', 'bar')

	def test_setdefault(self, ucr0):
		"""Test set ucr.setdefault()."""
		ucr0.setdefault('foo', 'bar')
		assert ucr0['foo'] == 'bar'

	def test_dict(self, ucrf):
		"""Test merged items."""
		assert dict(ucrf) == dict([('foo', 'FORCED'), ('bar', 'FORCED'), ('baz', 'NORMAL')])

	def test_items(self, ucrf):
		"""Test merged items."""
		assert sorted(ucrf.items()) == sorted([('foo', 'FORCED'), ('bar', 'FORCED'), ('baz', 'NORMAL')])

	def test_items_scopes(self, ucrf):
		"""Test merged items."""
		assert sorted(ucrf.items(getscope=True)) == sorted([('foo', (ConfigRegistry.FORCED, 'FORCED')), ('bar', (ConfigRegistry.FORCED, 'FORCED')), ('baz', (ConfigRegistry.NORMAL, 'NORMAL'))])

	@py2_only
	def test_iteritems(self, ucrf):
		"""Test merged items."""
		assert sorted(ucrf.iteritems()) == sorted([('foo', 'FORCED'), ('bar', 'FORCED'), ('baz', 'NORMAL')])

	def test_keys(self, ucrf):
		"""Test merged keys."""
		assert sorted(ucrf.keys()) == sorted(['foo', 'bar', 'baz'])

	@py2_only
	def test_iterkeys(self, ucrf):
		"""Test merged keys."""
		assert sorted(ucrf.iterkeys()) == sorted(['foo', 'bar', 'baz'])

	def test_values(self, ucrf):
		"""Test merged values."""
		assert sorted(ucrf.values()) == sorted(['FORCED', 'FORCED', 'NORMAL'])

	@py2_only
	def test_itervalues(self, ucrf):
		"""Test merged items."""
		assert sorted(ucrf.itervalues()) == sorted(['FORCED', 'FORCED', 'NORMAL'])

	def test_clear(self, ucrf):
		"""Test set ucr.clear()."""
		ucrf.clear()
		assert ucrf.get('foo', getscope=True) == (ConfigRegistry.FORCED, 'FORCED')
		assert ucrf.get('bar', getscope=True) == (ConfigRegistry.FORCED, 'FORCED')
		assert ucrf.get('baz', getscope=True) is None

	def test_is_true_unset(self, ucr0):
		"""Test unset is_true()."""
		assert not ucr0.is_true('foo')

	def test_is_true_default(self, ucr0):
		"""Test is_true(default)."""
		assert ucr0.is_true('foo', True)
		assert not ucr0.is_true('foo', False)

	@pytest.mark.parametrize("value", TRUE_VALID)
	def test_is_true_valid(self, value, ucr0):
		"""Test valid is_true()."""
		ucr0['foo'] = value
		assert ucr0.is_true('foo')

	@pytest.mark.parametrize("value", TRUE_INVALID)
	def test_is_true_invalid(self, value, ucr0):
		"""Test invalid is_true()."""
		ucr0['foo'] = value
		assert not ucr0.is_true('foo')

	@pytest.mark.parametrize("value", TRUE_VALID)
	def test_is_true_valid_direct(self, value, ucr0):
		"""Test valid is_true(value)."""
		assert ucr0.is_true(value=value)

	@pytest.mark.parametrize("value", TRUE_INVALID)
	def test_is_true_invalid_direct(self, value, ucr0):
		"""Test invalid is_true(value)."""
		assert not ucr0.is_true(value=value)

	def test_is_false_unset(self):
		"""Test unset is_false()."""
		ucr = ConfigRegistry()
		assert not ucr.is_false('foo')

	def test_is_false_default(self, ucr0):
		"""Test is_false(default)."""
		assert ucr0.is_false('foo', True)
		assert not ucr0.is_false('foo', False)

	@pytest.mark.parametrize("value", FALSE_VALID)
	def test_is_false_valid(self, value, ucr0):
		"""Test valid is_false()."""
		ucr0['foo'] = value
		assert ucr0.is_false('foo')

	@pytest.mark.parametrize("value", FALSE_INVALID)
	def test_is_false_invalid(self, value, ucr0):
		"""Test invalid is_false()."""
		ucr0['foo'] = value
		assert not ucr0.is_false('foo')

	@pytest.mark.parametrize("value", FALSE_VALID)
	def test_is_false_valid_direct(self, value, ucr0):
		"""Test valid is_false(value)."""
		assert ucr0.is_false(value=value)

	@pytest.mark.parametrize("value", FALSE_INVALID)
	def test_is_false_invalid_direct(self, value, ucr0):
		"""Test valid is_false(value)."""
		assert not ucr0.is_false(value=value)

	def test_update(self, ucr0):
		"""Test update()."""
		ucr0['foo'] = 'foo'
		ucr0['bar'] = 'bar'
		ucr0.update({
			'foo': None,
			'bar': 'baz',
			'baz': 'bar',
		})
		assert ucr0.get('foo') is None
		assert ucr0.get('bar') == 'baz'
		assert ucr0.get('baz') == 'bar'

	def test_locking(self, ucr0):
		"""Test inter-process-locking."""
		delay = 1.0
		read_end, write_end = os.pipe()

		pid1 = os.fork()
		if not pid1:  # child 1
			os.close(read_end)
			ucr0.lock()
			os.write(write_end, b'1')
			time.sleep(delay)
			ucr0.unlock()
			os._exit(0)

		pid2 = os.fork()
		if not pid2:  # child 2
			os.close(write_end)
			os.read(read_end, 1)
			ucr0.lock()
			time.sleep(delay)
			ucr0.unlock()
			os._exit(0)

		os.close(read_end)
		os.close(write_end)

		timeout = time.time() + delay * 3
		while time.time() < timeout:
			pid, status = os.waitpid(0, os.WNOHANG)
			if (pid, status) == (0, 0):
				time.sleep(0.1)
			elif pid == pid1:
				assert os.WIFEXITED(status) is True
				assert os.WEXITSTATUS(status) == 0
				pid1 = None
			elif pid == pid2:
				assert os.WIFEXITED(status) is True
				assert os.WEXITSTATUS(status) == 0
				assert pid1 is None, 'child 2 exited before child 1'
				break
			else:
				self.fail('Unknown child status: %d, %x' % (pid, status))
		else:
			self.fail('Timeout')
