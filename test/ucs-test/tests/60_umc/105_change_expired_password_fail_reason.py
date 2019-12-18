#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: Test detection of changing expired password failure reason
## exposure: dangerous
## packages: [univention-management-console-server]
## roles: [domaincontroller_master]
## tags: [skip_admember]

from __future__ import print_function

import pytest
import contextlib
from univention.config_registry import ConfigRegistry
from univention.admin.uldap import getAdminConnection
from univention.testing import utils

samba4_installed = utils.package_installed('univention-samba4')
ucr = ConfigRegistry()
ucr.load()
lo, pos = getAdminConnection()

REASON_TOO_SHORT = "Changing password failed. The password is too short."
REASON_TOO_SHORT_AT_LEAST_CHARACTERS = "Changing password failed. The password is too short. The password must consist of at least 8 characters."
REASON_TOO_SIMPLE = "Changing password failed. The password is too simple."
REASON_PALINDROME = "Changing password failed. The password is a palindrome."
REASON_DICTIONARY = "Changing password failed. The password is based on a dictionary word."
REASON_DIFFERENT_WORDS = 'Changing password failed. The password does not contain enough different characters.'
REASON_ALREADY_USED = 'Changing password failed. The password was already used.'
REASON_MINIMUM_AGE = 'Changing password failed. The minimum password age is not reached yet.'
REASON_TOO_SIMILAR = 'Changing password failed. The password is too similar to the old one.'

# TODO: add a lot more unimplemented tests!
reasons = {
	REASON_TOO_SHORT: ['Test', 'ana'],
	REASON_TOO_SHORT_AT_LEAST_CHARACTERS: [],
	REASON_TOO_SIMPLE: ['123456789'],
	REASON_PALINDROME: [],
	REASON_DICTIONARY: ['chocolate'],
	REASON_DIFFERENT_WORDS: ['ooooooooo'],
}
if samba4_installed:
	reasons = {
		REASON_TOO_SHORT: [],
		REASON_TOO_SHORT_AT_LEAST_CHARACTERS: ['Test', 'ana'],
		REASON_TOO_SIMPLE: ['123456789', 'chocolate', 'ooooooooo'],
		REASON_PALINDROME: [],
		REASON_DICTIONARY: [],
		REASON_DIFFERENT_WORDS: [],
	}


@contextlib.contextmanager
def enabled_password_quality_checks(ucr):
	# TODO: from 07_expired_password: only if univention-samba4 is not installed
	if samba4_installed:
		yield
		return
	ldap_base = ucr.get('ldap/base')
	dn = 'cn=default-settings,cn=pwhistory,cn=users,cn=policies,%s' % (ldap_base,)
	old = lo.getAttr(dn, 'univentionPWQualityCheck')
	new = ['TRUE']
	lo.modify(dn, [('univentionPWQualityCheck', old, new)])
	yield
	lo.modify(dn, [('univentionPWQualityCheck', new, old)])


@pytest.mark.parametrize('new_password,reason', [[y, reason] for reason, x in reasons.iteritems() for y in x])
def test_password_changing_failure_reason(new_password, reason, udm, Client, random_string, Unauthorized, ucr):
	print('test_password_changing_failure_reason(%r, %r)' % (new_password, reason))
	with enabled_password_quality_checks(ucr):
		_test_password_changing_failure_reason(new_password, reason, udm, Client, random_string, Unauthorized)


def _test_password_changing_failure_reason(new_password, reason, udm, Client, random_string, Unauthorized):
	password = random_string()
	userdn, username = udm.create_user(password=password, pwdChangeNextLogin=1)
	client = Client(language='en-US')
	if samba4_installed:
		utils.wait_for_connector_replication()
	print('change password from %r to %r' % (password, new_password))
	with pytest.raises(Unauthorized) as msg:
		client.umc_auth(username, password, new_password=new_password)
	assert reason == msg.value.message, 'Expected error %r but got %r' % (reason, msg.value.message)
