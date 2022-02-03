import passlib.hash

import univention.testing.udm as udm_test
import univention.testing.strings as uts
from univention.config_registry import handler_set as ucr_set
from univention.config_registry import handler_unset as ucr_unset

import pytest


@pytest.fixture(scope="session")
def rad_user(udm_session, ucr_session):
	old_ucr = ucr_session.get('radius/use-service-specific-password', None)
	password = uts.random_string()
	dn, name = udm_session.create_user(networkAccess=1, password=password, birthday='2001-01-01')
	yield dn, name, password

	# unset variable again
	if old_ucr:
		ucr_set(['radius/use-service-specific-password=%s' % (old_ucr,)])
	else:
		ucr_unset(['radius/use-service-specific-password'])


@pytest.fixture(scope="session")
def udm_session():
	with udm_test.UCSTestUDM() as udm:
		yield udm


@pytest.fixture
def ssp():
	password = uts.random_string().encode('utf-8')
	nt = passlib.hash.nthash.hash(password).upper().encode('utf-8')
	return password, nt
