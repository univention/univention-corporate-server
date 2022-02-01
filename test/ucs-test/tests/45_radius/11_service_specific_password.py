#!/usr/share/ucs-test/runner pytest-3 -s -vvv
## desc: check if service specific password works as expected
## tags: [apptest, radius]
## packages:
##   - univention-radius
## join: true
## exposure: dangerous

import ldap
import pytest
import subprocess
import passlib.hash

import univention.testing.strings as uts
import univention.testing.udm as udm_test
from univention.config_registry import handler_set as ucr_set
from univention.config_registry import handler_unset as ucr_unset


@pytest.fixture(scope="session")
def udm_session():
	with udm_test.UCSTestUDM() as udm:
		yield udm


@pytest.fixture(scope="session")
def rad_user(udm_session, ucr_session):
	old_ucr = ucr_session.get('radius/use-service-specific-password', None)
	password = uts.random_string()
	dn, name = udm_session.create_user(networkAccess=1, password=password)
	yield dn, name, password

	# unset variable again
	if old_ucr:
		ucr_set(['radius/use-service-specific-password=%s' % (old_ucr,)])
	else:
		ucr_unset(['radius/use-service-specific-password'])


def radius_auth(username, password):
	subprocess.check_call([
		'radtest',
		'-t',
		'mschap',
		username,
		password,
		'127.0.0.1:18120',
		'0',
		'testing123',
	])


@pytest.fixture(scope='session')
def ssp():
	password = uts.random_string().encode('utf-8')
	nt = passlib.hash.nthash.hash(password).upper().encode('utf-8')
	return password, nt


def test_radius_auth_nossp(udm_session, rad_user):
	dn, name, password = rad_user
	ucr_set(['radius/use-service-specific-password=false'])
	radius_auth(name, password)


# auth should fail with either password, there is no fallback
def test_radius_auth_no_ssp(rad_user, ssp):
	dn, name, password = rad_user
	ucr_set(['radius/use-service-specific-password=true'])
	with pytest.raises(subprocess.CalledProcessError):
		radius_auth(name, ssp[0])
	with pytest.raises(subprocess.CalledProcessError):
		radius_auth(name, password)


def test_radius_auth_ssp(rad_user, lo, ssp):
	dn, name, password = rad_user
	lo.modify_ext_s(dn, ((ldap.MOD_ADD, 'objectclass', b'univentionPerson'), (ldap.MOD_REPLACE, 'univentionRadiusPassword', ssp[1])))
	ucr_set(['radius/use-service-specific-password=true'])
	radius_auth(name, ssp[0])
