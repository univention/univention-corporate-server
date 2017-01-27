import pytest
from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.udm import UCSTestUDM
from univention.testing.utils import verify_ldap_object as _verify_ldap_object, get_ldap_connection
from univention.testing.umc import Client as _Client
import univention.lib.umc


@pytest.fixture(scope="module")
def ucr():
	ucr = UCSTestConfigRegistry()
	ucr.load()
	return ucr


@pytest.fixture(scope="module")
def server_role(ucr):
	return ucr.get('server/role')


@pytest.fixture(scope="module")
def ldap_base(ucr):
	return ucr.get('ldap/base')


@pytest.fixture(scope="module")
def ldap_master(ucr):
	return ucr.get('ldap/master')


@pytest.fixture(scope="module")
def UDM():
	return UCSTestUDM


@pytest.fixture(scope="module")
def Client():
	return _Client


@pytest.fixture(scope="module")
def lo():
	return get_ldap_connection()


@pytest.fixture(scope="module")
def verify_ldap_object():
	return _verify_ldap_object


@pytest.fixture()
def ServiceUnavailable():
	return univention.lib.umc.ServiceUnavailable


@pytest.fixture()
def ConnectionError():
	return univention.lib.umc.ConnectionError


@pytest.fixture()
def HTTPError():
	return univention.lib.umc.HTTPError
