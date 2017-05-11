#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: Test detection of changing expired password failure reason
## exposure: dangerous
## packages: [univention-management-console-server]

import pytest
from univention.config_registry import handler_set
from univention.testing import utils


@pytest.yield_fixture()
def enabled_password_quality_checks(lo, ldap_base, ucr):
	# TODO: from 07_expired_password: only if univention-samba4 is not installed
	dn = 'cn=default-settings,cn=pwhistory,cn=users,cn=policies,%s' % (ldap_base,)
	old = lo.getAttr(dn, 'univentionPWQualityCheck')
	new = ['TRUE']
	lo.modify(dn, [('univentionPWQualityCheck', old, new)])
	handler_set(['password/quality/credit/lower=1', 'password/quality/credit/upper=1', 'password/quality/credit/other=1', 'password/quality/credit/digits=1'])
	yield
	lo.modify(dn, [('univentionPWQualityCheck', new, old)])


def test_password_changing_failure_reason(options, new_password, reason, udm, Client, random_string, Unauthorized):
	password = random_string()
	userdn, username = udm.create_user(options=options, password=password, pwdChangeNextLogin=1)
	client = Client()
	print 'change password from %r to %r' % (password, new_password)
	with pytest.raises(Unauthorized) as msg:
		client.umc_auth(username, password, new_password=new_password)
	assert msg.value.message == reason


def pytest_generate_tests(metafunc):
	if metafunc.function.__name__ != 'test_password_changing_failure_reason':
		return

	samba4_installed = utils.package_installed('univention-samba4')
	data = []
	# pam_unix
	for option in [[], ['posix'], ['posix', 'samba']]:
		new_password = 'Test'
		reason = "Changing password failed. The password is too short."
		data.append([option, new_password, reason])

		new_password = 'ana'
		reason = "Changing password failed. The password is too short."
		data.append([option, new_password, reason])

	# pam_krb5
	for option in [['kerberos', 'person']]:
		new_password = 'Test'
		reason = "Changing password failed. The password is too simple."
		data.append([option, new_password, reason])

		new_password = 'ana'
		reason = "Changing password failed. The password is a palindrome."
		data.append([option, new_password, reason])

	for option in [[], ['posix', 'samba'], ['kerberos', 'person'], ['posix']]:
		new_password = 'chocolate'
		reason = "Changing password failed. The password is too simple." if samba4_installed else "Changing password failed. The password is based on a dictionary word."
		data.append([option, new_password, reason])

	metafunc.parametrize('options,new_password,reason', data)
