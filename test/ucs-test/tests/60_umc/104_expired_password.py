#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: Test UMC authentication with expired accounts
## exposure: dangerous
## packages: [univention-management-console-server]

import pytest
from univention.testing import utils

# TODO: test detection of expired password + account disabled + both
# TODO: test password history, complexity, length


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
		self.assert_password_expired(msg.value)

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
		self.assert_password_expired(msg.value)

	def assert_password_expired(self, exc):
		assert exc.status == 401
		assert exc.result['password_expired']
		assert exc.message == "The password has expired and must be renewed."

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
