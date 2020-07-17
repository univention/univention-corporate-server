import sys
from os.path import dirname, join, pardir

import pytest

sys.path.insert(0, join(dirname(__file__), pardir, 'python'))
from univention.config_registry.backend import ConfigRegistry  # noqa E402


@pytest.fixture
def ucr0(tmpdir):
	"""
	Return an empty UCR instance.
	"""
	ConfigRegistry.PREFIX = str(tmpdir)
	ucr = ConfigRegistry()
	return ucr


@pytest.fixture
def ucrf(ucr0):
	"""
	Return a pre-initialized UCR instance.
	"""
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
