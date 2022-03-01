#!/usr/share/ucs-test/runner pytest-3 -s -vvv
## desc: SSO Login at UMC, test umc connection and ldap connection
## tags: [saml]
## roles: [domaincontroller_master]
## join: true
## exposure: safe
## tags:
##  - skip_admember

import subprocess
import time

import univention.testing.utils as utils

import samltest


def __get_samlSession():
	account = utils.UCSTestDomainAdminCredentials()
	return samltest.SamlTest(account.username, account.bindpw)


def __test_umc_sp(samlSession, test_function):
	samlSession.login_with_new_session_at_IdP()
	test_function()
	samlSession.logout_at_IdP()
	samlSession.test_logout_at_IdP()
	samlSession.test_logout()


def test_umc_server():
	def assert_module_testing():
		# Ensure a umc module will be opened
		subprocess.check_call(['systemctl', 'stop', 'univention-management-console-server'])
		samlSession.test_umc_server()

	samlSession = __get_samlSession()
	try:
		__test_umc_sp(samlSession, assert_module_testing)
	except samltest.SamlError:
		if samlSession.page.status_code == 503:
			pass
		else:
			raise
	else:
		utils.fail('test_umc_server() should not work without umc server running')
	finally:
		subprocess.check_call(['systemctl', 'start', 'univention-management-console-server'])
		time.sleep(3)  # umc-server is not ready immediately

	samlSession = __get_samlSession()
	__test_umc_sp(samlSession, samlSession.test_umc_server)


def test_umc_ldap_con():
	def assert_slapd_testing():
		samlSession.test_slapd()
		# Ensure an ldap connection will be opened
		subprocess.check_call(['systemctl', 'stop', 'slapd'])
		samlSession.test_slapd()

	try:
		samlSession = __get_samlSession()
		__test_umc_sp(samlSession, assert_slapd_testing)
	except samltest.SamlError:
		if samlSession.page.status_code == 503:
			pass
		else:
			raise
	else:
		utils.fail('test_slapd() should not work without slapd running')
	finally:
		subprocess.check_call(['systemctl', 'start', 'slapd'])

	for _ in range(2):
		samlSession = __get_samlSession()
		__test_umc_sp(samlSession, samlSession.test_slapd)
