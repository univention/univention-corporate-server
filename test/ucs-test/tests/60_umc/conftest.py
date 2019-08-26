import pytest
from univention.testing import ucr as _ucr, udm as _udm, utils, umc, strings
import univention.lib.umc


@pytest.yield_fixture()
def ucr():
	with _ucr.UCSTestConfigRegistry() as ucr:
		yield ucr


@pytest.fixture(scope="module")
def server_role(ucr):
	return ucr.get('server/role')


@pytest.fixture(scope="module")
def ldap_base(ucr):
	return ucr.get('ldap/base')


@pytest.fixture(scope="module")
def ldap_master(ucr):
	return ucr.get('ldap/master')


@pytest.yield_fixture()
def udm():
	with _udm.UCSTestUDM() as udm:
		yield udm


@pytest.fixture(scope="module")
def Client():
	return umc.Client


@pytest.fixture(scope="module")
def lo():
	return utils.get_ldap_connection()


@pytest.fixture(scope="module")
def verify_ldap_object():
	return utils.verify_ldap_object


@pytest.fixture(scope="module")
def verify_udm_object():
	return _udm.verify_udm_object


@pytest.fixture()
def ServiceUnavailable():
	return univention.lib.umc.ServiceUnavailable


@pytest.fixture()
def ConnectionError():
	return univention.lib.umc.ConnectionError


@pytest.fixture()
def Unauthorized():
	return univention.lib.umc.Unauthorized


@pytest.fixture()
def HTTPError():
	return univention.lib.umc.HTTPError


@pytest.fixture
def random_string():
	return strings.random_string


@pytest.fixture
def random_name():
	return strings.random_name


@pytest.fixture
def random_username():
	return strings.random_username


@pytest.fixture
def wait_for_replication():
	return utils.wait_for_replication
