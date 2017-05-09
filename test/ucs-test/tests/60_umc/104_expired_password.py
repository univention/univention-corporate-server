#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: Test UMC authentication with expired accounts
## exposure: dangerous
## packages: [univention-management-console-server]

import pytest
from univention.testing import utils
from univention.config_registry import handler_set

# TODO: test detection of expired password + account disabled + both
# TODO: test password history, complexity, length


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


class TestPwdChangeNextLogin(object):
	"""
	Ensure that the UMC PAM configuration for pam_unix.so + pam_krb5.so is correct.
	This is tested by UMC authenticating a user with pwdChangeNextLogin=1 (only for options: posix, samba, kerberos).
	pam_ldap is therefore untested!
	"""

	PWD_CHANGE_NEXT_LOGIN_OPTIONS = [
		[], ['posix', 'samba'], ['kerberos', 'person'],
		['posix'],
		pytest.mark.xfail(reason='https://forge.univention.org/bugzilla/show_bug.cgi?id=34481')(['samba']),
		pytest.mark.xfail(reason='https://forge.univention.org/bugzilla/show_bug.cgi?id=34481')(['kerberos']),
	]

	@pytest.mark.parametrize('options', PWD_CHANGE_NEXT_LOGIN_OPTIONS)
	def test_expired_password_detection_create_pwdchangenextlogin(self, options, udm, Client, random_string, Unauthorized):
		password = random_string()
		userdn, username = udm.create_user(options=options, password=password, pwdChangeNextLogin=1)
		client = Client()
		with pytest.raises(Unauthorized) as msg:
			client.authenticate(username, password)
		assert msg.value.result['password_expired']
		assert msg.value.message == "The password has expired and must be renewed."

	@pytest.mark.parametrize('options', PWD_CHANGE_NEXT_LOGIN_OPTIONS)
	def test_expired_password_detection_modify_pwdchangenextlogin(self, options, udm, Client, random_string, Unauthorized):
		password = random_string()
		userdn, username = udm.create_user(options=options, password=password)
		client = Client()
		client.authenticate(username, password)

		udm.modify_object('users/user', dn=userdn, pwdChangeNextLogin=1)

		client = Client()
		with pytest.raises(Unauthorized) as msg:
			client.authenticate(username, password)
		assert msg.value.result['password_expired']
		assert msg.value.message == "The password has expired and must be renewed."

	@pytest.mark.parametrize('options', PWD_CHANGE_NEXT_LOGIN_OPTIONS)
	def test_change_password(self, options, udm, Client, random_string, Unauthorized, wait_for_replication):
		password = random_string()
		new_password = random_string()
		userdn, username = udm.create_user(options=options, password=password, pwdChangeNextLogin=1)
		client = Client()
		print 'change password from %r to %r' % (password, new_password)
		client.umc_auth(username, password, new_password=new_password)

		wait_for_replication()

		print 'check login with new password'
		client = Client()
		client.authenticate(username, new_password)

		print 'ensure login with old password does not work anymore'
		with pytest.raises(Unauthorized):
			client = Client()
			client.authenticate(username, password)

	def test_changing_too_short_password_fail(self, options, new_password, reason, udm, Client, random_string, Unauthorized):
		password = random_string()
		userdn, username = udm.create_user(options=options, password=password, pwdChangeNextLogin=1)
		client = Client()
		print 'change password from %r to %r' % (password, new_password)
		with pytest.raises(Unauthorized) as msg:
			client.umc_auth(username, password, new_password=new_password)
		assert msg.value.message == reason


def pytest_generate_tests(metafunc):
	if metafunc.function.__name__ != 'test_changing_too_short_password_fail':
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


class TestBasics(object):

	def test_login_invalid_user(self, udm, Client, random_string, Unauthorized):
		password = random_string()
		userdn, username = udm.create_user(password=password)
		with pytest.raises(Unauthorized):
			client = Client()
			client.authenticate('UNKNOWN' + username, password)

	def test_login_invalid_password(self, udm, Client, random_string, Unauthorized):
		password = random_string()
		userdn, username = udm.create_user(password=password)
		with pytest.raises(Unauthorized):
			client = Client()
			client.authenticate(username, password + 'INVALID')

	def test_login_as_root(self, Client):
		client = Client()
		# Actually this is the password of the Administrator account but probably in most test scenarios also the root password
		client.authenticate('root', utils.UCSTestDomainAdminCredentials().bindpw)


class TestLDAPUsers(object):
	"""Ensure pam_ldap.so works and the PAM configuration for LDAP users is not disturbed by pam_unix.so / pam_ldap.so)"""

	def test_ldap_pwd_user_umc_authentication(self, udm, Client, random_string, Unauthorized):
		password = random_string()
		userdn, username = udm.create_user(options=['ldap_pwd'], password=password)
		client = Client()
		client.authenticate(username, password)
