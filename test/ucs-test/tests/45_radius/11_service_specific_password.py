#!/usr/share/ucs-test/runner pytest-3 -s -vvv
## desc: check if service specific password works as expected
## tags: [apptest, radius]
## packages:
##   - univention-radius
## join: true
## exposure: dangerous

import json
import ldap
import urllib
import pytest
import requests
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


def request_new_password(ucr, user_dn, service={"service": "radius"}):
	dn = urllib.parse.quote_plus(user_dn)
	headers = {"Accept": "application/json", "Content-Type": "application/json"}
	#TODO: not do it via Administrator
	auth = (ucr.get("users/default/administrator", "Administrator"), ucr.get("tests/domainadmin/pwd"))
	resp = requests.post("https://localhost/univention/udm/users/user/%s/service-specific-password" % (dn,), auth=auth, json=service, headers=headers, verify=False)
	if not resp.ok:
		print(resp.text)
		raise AssertionError("Received Error %s" % (resp.text,))
	return json.loads(resp.text).get('password')


def test_udm_rest(ucr, udm_session, rad_user):
	dn, name, password = rad_user
	new_password = request_new_password(ucr, dn)
	ucr_set(['radius/use-service-specific-password=true'])
	with pytest.raises(subprocess.CalledProcessError):
		radius_auth(name, password)
	radius_auth(name, new_password)


def test_udm_rest_invalid_service(ucr, udm_session, rad_user):
	dn, name, password = rad_user
	with pytest.raises(AssertionError):
		request_new_password(ucr, dn, service={"service": "testtest"})


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
