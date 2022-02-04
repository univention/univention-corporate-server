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

from univention.config_registry import handler_set as ucr_set


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

# Check if radius auth works with userpassword, when ssp is disabled
def test_radius_auth_without_ssp(udm_session, rad_user):
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
	lo.modify_ext_s(dn, ((ldap.MOD_REPLACE, 'univentionRadiusPassword', ssp[1]),))
	ucr_set(['radius/use-service-specific-password=true'])
	radius_auth(name, ssp[0])
