import subprocess
import time
from typing import Callable, Iterator, Type  # noqa F401

import pytest

import univention.lib.umc
from univention.testing import strings, ucr as _ucr, udm as _udm, umc, utils, selenium as _sel

pytest_plugins = ["univention.testing.conftest"]


@pytest.fixture()
def ucr():
	# type: () -> Iterator[_ucr.UCSTestConfigRegistry]
	"""
	Per `function` auto-reverting UCR instance.
	"""
	with _ucr.UCSTestConfigRegistry() as ucr:
		yield ucr


@pytest.fixture(scope='session')
def ucr_session():
	# type: () -> Iterator[_ucr.UCSTestConfigRegistry]
	"""
	Per `session` auto-reverting UCR instance.
	"""
	with _ucr.UCSTestConfigRegistry() as ucr:
		yield ucr


@pytest.fixture(scope='session')
def restart_s4connector_if_present():
	# type: () -> Callable[[], None]
	"""
	Function to restart S4 connector if present.
	"""
	def restart():
		if utils.s4connector_present():
			print('restarting s4 connector')
			utils.restart_s4connector()
	return restart


@pytest.fixture(scope='session')
def restart_umc_server():
	# type: () -> Callable[[], None]
	"""
	Function to restart UMC server.
	"""
	def _restart_umc_server():
		subprocess.call(['systemctl', 'restart', 'univention-management-console-server.service'])
		time.sleep(2)
	return _restart_umc_server


@pytest.fixture(scope='session')
def server_role(ucr_session):
	# type: (...) -> str
	"""
	UCS server role string from UCR.
	"""
	return ucr_session.get('server/role')


@pytest.fixture(scope='session')
def ldap_base(ucr_session):
	# type: (...) -> str
	"""
	LDAP base DN string from UCR.
	"""
	return ucr_session.get('ldap/base')


@pytest.fixture(scope='session')
def ldap_master(ucr_session):
	# type: (...) -> str
	"""
	LDAP primary name from UCR.
	"""
	return ucr_session.get('ldap/master')


@pytest.fixture()
def udm():
	# type: () -> Iterator[_udm.UCSTestUDM]
	"""
	Auto-reverting UDM wrapper.
	"""
	with _udm.UCSTestUDM() as udm:
		yield udm


@pytest.fixture
def selenium():
	# type: () -> Iterator[_sel.UMCSeleniumTest]
	"""
	Browser based testing for UMC using Selenium.
	"""
	with _sel.UMCSeleniumTest() as s:
		yield s


@pytest.fixture(scope='session')
def Client():
	# type: () -> Type[umc.Client]
	"""
	Session scoped client factory to access UMC.
	"""
	return umc.Client


@pytest.fixture(scope="module")
def lo():
	# type: () -> univention.admin.uldap.access
	"""
	Module scoped LDAP connection.
	"""
	return utils.get_ldap_connection()


@pytest.fixture(scope='session')
def verify_ldap_object():
	# type: () -> Callable[..., None]
	"""
	Function to verify LDAP entries.
	"""
	return utils.verify_ldap_object


@pytest.fixture(scope='session')
def verify_udm_object():
	# type: () -> Callable[..., None]
	"""
	Function to verify UDM objects.
	"""
	return _udm.verify_udm_object


@pytest.fixture(scope='session')
def random_string():
	# type: () -> Callable[..., str]
	"""
	Function to generate random string.
	"""
	return strings.random_string


@pytest.fixture(scope='session')
def random_name():
	# type: () -> Callable[..., str]
	"""
	Function to generate random name.
	"""
	return strings.random_name


@pytest.fixture(scope='session')
def random_username():
	# type: () -> Callable[..., str]
	"""
	Function to generate random user name.
	"""
	return strings.random_username


@pytest.fixture(scope='session')
def wait_for_replication():
	# type: () -> Callable[..., None]
	"""
	Function to wait for replication to finish.
	"""
	return utils.wait_for_replication
