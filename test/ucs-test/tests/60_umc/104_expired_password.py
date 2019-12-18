#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: Test UMC authentication with expired accounts
## exposure: dangerous
## packages: [univention-management-console-server]
## roles: [domaincontroller_master, domaincontroller_backup]
## tags: [skip_admember]

from __future__ import print_function

import pytest
import time
from univention.testing import utils
from ldap.filter import filter_format
# TODO: test detection of expired password + account disabled + both
# TODO: test password history, complexity, length

from univention.testing.ucs_samba import wait_for_drs_replication

samba4_installed = utils.package_installed('univention-samba4')


class TestPwdChangeNextLogin(object):
	"""
	Ensure that the UMC PAM configuration for pam_unix.so + pam_krb5.so is correct.
	This is tested by UMC authenticating a user with pwdChangeNextLogin=1
	pam_ldap is therefore untested!
	"""

	PWD_CHANGE_NEXT_LOGIN_OPTIONS = [
		[],  # TODO: test without mail, person,
	]

	@pytest.mark.parametrize('options', PWD_CHANGE_NEXT_LOGIN_OPTIONS)
	def test_expired_password_detection_create_pwdchangenextlogin(self, options, udm, Client, random_string, Unauthorized):
		print('test_expired_password_detection_create_pwdchangenextlogin(%r)' % (options,))
		password = random_string()
		userdn, username = udm.create_user(options=options, password=password, pwdChangeNextLogin=1)
		client = Client(language='en-US')
		with pytest.raises(Unauthorized) as msg:
			client.authenticate(username, password)
		self.assert_password_expired(msg.value)

	@pytest.mark.parametrize('options', PWD_CHANGE_NEXT_LOGIN_OPTIONS)
	def test_expired_password_detection_modify_pwdchangenextlogin(self, options, udm, Client, random_string, Unauthorized):
		print('test_expired_password_detection_modify_pwdchangenextlogin(%r)' % (options,))
		password = random_string()
		userdn, username = udm.create_user(options=options, password=password)
		client = Client(language='en-US')
		client.authenticate(username, password)

		udm.modify_object('users/user', dn=userdn, pwdChangeNextLogin=1)

		client = Client(language='en-US')
		with pytest.raises(Unauthorized) as msg:
			client.authenticate(username, password)
		self.assert_password_expired(msg.value)

	def assert_password_expired(self, exc):
		assert exc.status == 401
		assert exc.result and exc.result.get('password_expired'), 'Password was not detected as expired: %s' % (exc.result,)
		assert exc.message == "The password has expired and must be renewed."

	@pytest.mark.parametrize('options', [
		[],
	])
	def test_change_password(self, options, udm, Client, random_string, Unauthorized, wait_for_replication):
		print('test_change_password(%r)' % (options,))
		password = random_string()
		new_password = random_string(5) + random_string(5).upper() + '@99'
		userdn, username = udm.create_user(options=options, password=password, pwdChangeNextLogin=1)
		if samba4_installed:
			utils.wait_for_connector_replication()
			wait_for_drs_replication(filter_format('sAMAccountName=%s', [username]))

		client = Client(language='en-US')
		print('check login with pwdChangeNextLogin=1')
		with pytest.raises(Unauthorized):
			client.umc_auth(username, password)

		client = Client(language='en-US')
		print('change password from %r to %r' % (password, new_password))
		client.umc_auth(username, password, new_password=new_password)

		wait_for_replication()
		if samba4_installed:
			utils.wait_for_connector_replication()
			wait_for_drs_replication(filter_format('(&(sAMAccountName=%s)(!(pwdLastSet=0)))', [username]))
			# fails on backup because the user account in the local ldap has still shadowMax=1
			# we set the password via krb5 -> samba, now drs replication to the master, s4 connector
			# on the master and LDAP replication to the backup, no way to wait for that
			# best would be to check the local ldap backup for NOT shadowMax=1, but sleep also works for now
			time.sleep(30)

		print('check login with new password')
		client = Client(language='en-US')
		client.authenticate(username, new_password)

		print('ensure login with old password does not work anymore')
		with pytest.raises(Unauthorized):
			client = Client(language='en-US')
			client.authenticate(username, password)


class TestBasics(object):

	def test_login_invalid_user(self, udm, Client, random_string, Unauthorized):
		password = random_string()
		userdn, username = udm.create_user(password=password)
		with pytest.raises(Unauthorized):
			client = Client(language='en-US')
			client.authenticate('UNKNOWN' + username, password)

	def test_login_invalid_password(self, udm, Client, random_string, Unauthorized):
		password = random_string()
		userdn, username = udm.create_user(password=password)
		with pytest.raises(Unauthorized):
			client = Client(language='en-US')
			client.authenticate(username, password + 'INVALID')

	def test_login_as_root(self, Client):
		client = Client(language='en-US')
		# Actually this is the password of the Administrator account but probably in most test scenarios also the root password
		client.authenticate('root', utils.UCSTestDomainAdminCredentials().bindpw)


class TestLDAPUsers(object):
	"""Ensure pam_ldap.so works and the PAM configuration for LDAP users is not disturbed by pam_unix.so / pam_ldap.so)"""

	def test_ldap_pwd_user_umc_authentication(self, udm, Client, random_string, Unauthorized):
		password = random_string()
		userdn, username = udm.create_ldap_user(password=password)
		client = Client(language='en-US')
		client.authenticate(username, password)
