#!/usr/share/ucs-test/runner /usr/bin/py.test
# -*- coding: utf-8 -*-
## desc: Test UDM APIs LDAP connection initialization feature
## exposure: dangerous
## roles: [domaincontroller_master]
## tags: [udm_api, skip_admember]
## packages: [python-univention-directory-manager]
## bugs: [47316]

import os
from subprocess import call
from unittest import main, TestCase
import univention.debug as ud
from univention.testing.udm import UCSTestUDM
from univention.testing.ucr import UCSTestConfigRegistry
import univention.testing.strings as uts
from univention.udm import UDM, ConnectionError, NoApiVersionSet, ApiVersionMustNotChange, ApiVersionNotSupported
from univention.udm.connections import LDAP_connection


ud.init('/var/log/univention/directory-manager-cmd.log', ud.FLUSH, 0)
ud.set_level(ud.ADMIN, ud.ALL)


class TestUdmAutoOpen(TestCase):
	ucr_test = None
	udm_test = None

	@classmethod
	def setUpClass(cls):
		cls.udm_test = UCSTestUDM()
		cls.ucr_test = UCSTestConfigRegistry()
		cls.ucr_test.load()

	@classmethod
	def tearDownClass(cls):
		cls.ucr_test.revert_to_original_registry()
		cls.udm_test.cleanup()

	@classmethod
	def setUp(self):
		LDAP_connection._clear()

	def test_error_in_version(self):
		with self.assertRaises(NoApiVersionSet):
			UDM.admin().get('users/user')
		with self.assertRaises(ApiVersionNotSupported):
			UDM.admin().version('1')
		with self.assertRaises(ApiVersionMustNotChange):
			UDM.admin().version(0).version(1)
		with self.assertRaises(ApiVersionNotSupported):
			UDM.admin().version(20).get('users/user')

	def test_admin(self):
		mod = UDM.admin().version(0).get('users/user')
		assert mod.connection.binddn == 'cn=admin,{}'.format(self.ucr_test['ldap/base'])

	def test_admin_io_error(self):
		try:
			os.rename('/etc/ldap.secret', '/etc/ldap.secret.test')
			with self.assertRaises(ConnectionError) as cm:
				UDM.admin()
			assert str(cm.exception) == 'Could not read secret file'
		finally:
			os.rename('/etc/ldap.secret.test', '/etc/ldap.secret')

	def test_machine(self):
		mod = UDM.machine().version(0).get('users/user')
		assert mod.connection.binddn == self.ucr_test['ldap/hostdn']

	def test_machine_down_error(self):
		assert call(['systemctl', 'stop', 'slapd']) == 0
		try:
			with self.assertRaises(ConnectionError) as cm:
				UDM.machine()
			assert str(cm.exception) == 'The LDAP Server is not running'
		finally:
			assert call(['systemctl', 'start', 'slapd']) == 0

	def test_machine_credentials_error(self):
		pw = open('/etc/machine.secret').read()
		try:
			open('/etc/machine.secret', 'w').write('garbage')
			with self.assertRaises(ConnectionError) as cm:
				UDM.machine()
			assert str(cm.exception) == 'Credentials invalid'
		finally:
			open('/etc/machine.secret', 'w').write(pw)

	def test_credentials(self):
		password = uts.random_name()
		dn, username = self.udm_test.create_user(password=password)
		mod = UDM.credentials(identity=username, password=password).version(0).get('users/user')
		assert mod.connection.binddn == dn

		password = uts.random_name()
		dn, username = self.udm_test.create_user(password=password)
		mod = UDM.credentials(identity=dn, password=password).version(0).get('users/user')
		assert mod.connection.binddn == dn

	def test_local(self):
		password = uts.random_name()
		dn, username = self.udm_test.create_user(password=password)
		server = self.ucr_test['ldap/server/name']
		port = self.ucr_test['ldap/server/port']
		mod = UDM.credentials(identity=username, password=password, server=server, port=port).version(0).get('users/user')
		assert mod.connection.binddn == dn

	def test_credentials_error(self):
		username = uts.random_name()
		password = uts.random_name()
		with self.assertRaises(ConnectionError) as cm:
			UDM.credentials(identity=username, password=password)
		assert str(cm.exception) == 'Cannot get DN for username'

		with self.assertRaises(ConnectionError) as cm:
			UDM.credentials(identity='Administrator', password=password)
		assert str(cm.exception) == 'Credentials invalid'

if __name__ == '__main__':
	main(verbosity=2)
