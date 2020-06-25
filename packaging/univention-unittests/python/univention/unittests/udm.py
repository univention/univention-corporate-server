import pytest

from univention.unittests import import_module
from univention.unittests.udm_database import Database
from univention.unittests.udm_connection import mock_conn, MockedAccess, MockedPosition  # noqa: F401


def pytest_addoption(parser):
	parser.addoption("--installed-udm", action="store_true", help="Test against installed UDM installation (not src)")


def import_udm_module(udm_path):
	python_module_name = 'univention.admin.{}'.format(udm_path)
	umc_src_path = 'modules/univention/admin'
	use_installed = pytest.config.getoption('--installed-udm')
	return import_module(udm_path, umc_src_path, python_module_name, use_installed)


@pytest.fixture
def ldap_database_file():
	return None


@pytest.fixture
def ldap_database(ldap_database_file, empty_ldap_database):
	if ldap_database_file:
		empty_ldap_database.fill(ldap_database_file)
	return empty_ldap_database


@pytest.fixture
def empty_ldap_database():
	database = Database()
	return database
