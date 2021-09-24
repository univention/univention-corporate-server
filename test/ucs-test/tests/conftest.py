import subprocess
import time

import pytest

import univention.lib.umc
from univention.testing import strings, ucr as _ucr, udm as _udm, umc, utils

pytest_plugins = ["univention.testing.conftest"]


@pytest.fixture()
def ucr():  # type: () -> _ucr.UCSTestConfigRegistry
	with _ucr.UCSTestConfigRegistry() as ucr:
		yield ucr


@pytest.fixture(scope='session')
def ucr_session():  # type: () -> _ucr.UCSTestConfigRegistry
	with _ucr.UCSTestConfigRegistry() as ucr:
		yield ucr


@pytest.fixture(scope='session')
def restart_s4connector_if_present():
	def restart():
		if utils.s4connector_present():
			print('restarting s4 connector')
			utils.restart_s4connector()
	return restart


@pytest.fixture(scope='session')
def restart_umc_server():
	def _restart_umc_server():
		subprocess.call(['systemctl', 'restart', 'univention-management-console-server.service'])
		time.sleep(2)
	return _restart_umc_server


@pytest.fixture(scope='session')
def server_role(ucr_session):
	return ucr_session.get('server/role')


@pytest.fixture(scope='session')
def ldap_base(ucr_session):  # type: () -> str
	return ucr_session.get('ldap/base')


@pytest.fixture(scope='session')
def ldap_master(ucr_session):
	return ucr_session.get('ldap/master')


@pytest.fixture()
def udm():
	with _udm.UCSTestUDM() as udm:
		yield udm


@pytest.fixture(scope='session')
def Client():
	return umc.Client


@pytest.fixture(scope="module")
def lo():
	return utils.get_ldap_connection()


@pytest.fixture(scope='session')
def verify_ldap_object():
	return utils.verify_ldap_object


@pytest.fixture(scope='session')
def verify_udm_object():
	return _udm.verify_udm_object


@pytest.fixture(scope='session')
def ServiceUnavailable():
	return univention.lib.umc.ServiceUnavailable


@pytest.fixture(scope='session')
def ConnectionError():
	return univention.lib.umc.ConnectionError


@pytest.fixture(scope='session')
def Unauthorized():
	return univention.lib.umc.Unauthorized


@pytest.fixture(scope='session')
def HTTPError():
	return univention.lib.umc.HTTPError


@pytest.fixture(scope='session')
def random_string():
	return strings.random_string


@pytest.fixture(scope='session')
def random_name():
	return strings.random_name


@pytest.fixture(scope='session')
def random_username():
	return strings.random_username


@pytest.fixture(scope='session')
def wait_for_replication():
	return utils.wait_for_replication
