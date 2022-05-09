import sys
from os.path import dirname, join, pardir

import pytest

sys.path.insert(0, join(dirname(__file__), pardir, 'python'))
import univention.config_registry.backend as be  # noqa: E402
import univention.config_registry.handler as h  # noqa: E402


@pytest.fixture(autouse=True)
def ucr0(tmpdir, monkeypatch, request):
	"""
	Return an empty UCR instance.
	"""
	monkeypatch.setattr(be.ReadOnlyConfigRegistry, "PREFIX", str(tmpdir))
	marker = request.node.get_closest_marker("ucr_layer")
	if marker is None:
		ucr = be.ConfigRegistry()
	else:
		ucr = be.ConfigRegistry(write_registry=marker.args[0])
	return ucr


@pytest.fixture
def ucrf(ucr0):
	"""
	Return a pre-initialized UCR instance.
	"""
	ucr = be.ConfigRegistry(write_registry=be.ConfigRegistry.LDAP)
	ucr['foo'] = 'LDAP'
	ucr['bar'] = 'LDAP'
	ucr.save()
	ucr = be.ConfigRegistry()
	ucr['bar'] = 'NORMAL'
	ucr['baz'] = 'NORMAL'
	ucr.save()
	ucr0.load()
	return ucr0


@pytest.fixture
def tmpucr(monkeypatch, tmpdir):
	fname = tmpdir / 'custom.conf'
	monkeypatch.setenv('UNIVENTION_BASECONF', str(fname))
	return fname


@pytest.fixture(autouse=True)
def tmpcache(monkeypatch, tmpdir):
	fname = tmpdir / 'cache'
	monkeypatch.setattr(h.ConfigHandlers, "CACHE_FILE", str(fname))
	return fname
