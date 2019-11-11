#!/usr/share/ucs-test/runner /usr/bin/py.test
# -*- coding: utf-8 -*-
## desc: Test UDM API for users/user module
## exposure: dangerous
## roles: [domaincontroller_master]
## tags: [udm_api]
## packages: [python-univention-directory-manager]
## bugs: [47316]

from collections import namedtuple
from unittest import main, TestCase
import univention.debug as ud
from univention.udm import UDM
from univention.testing.ucr import UCSTestConfigRegistry
from univention.udm.exceptions import MoveError


ud.init('/var/log/univention/directory-manager-cmd.log', ud.FLUSH, 0)
ud.set_level(ud.ADMIN, ud.ALL)


PostalAddress = namedtuple('PostalAddress', ['street', 'zipcode', 'city'])


class TestUdmUsersBasic(TestCase):
	@classmethod
	def setUpClass(cls):
		cls.udm = UDM.admin().version(1)
		cls.ucr_test = UCSTestConfigRegistry()
		cls.ucr_test.load()

	def test_cleanup(self):
		ubuntu = self.udm.get('computers/ubuntu').new()
		ubuntu.props.name = 'ubuntu'
		ubuntu.props.network = 'cn=default,cn=networks,%s' % self.ucr_test['ldap/base']
		ubuntu.save()
		try:
			num_ptr_records = len(list(self.udm.get('dns/ptr_record').search()))
			ip = ubuntu.props.ip[0]
			forward_zone = list(self.udm.get('dns/forward_zone').search())[0]
			reverse_zone = list(self.udm.get('dns/reverse_zone').search())[0]
			ubuntu.props.dnsEntryZoneForward = [[forward_zone.dn, ip]]
			ubuntu.props.dnsEntryZoneReverse = [[reverse_zone.dn, ip]]
			ubuntu.save()
			# assert newly created ptr record
			assert num_ptr_records + 1 == len(list(self.udm.get('dns/ptr_record').search()))
			ubuntu.delete()
			assert num_ptr_records == len(list(self.udm.get('dns/ptr_record').search()))
		finally:
			ubuntu.delete()

	def test_move_error(self):
		ubuntu = self.udm.get('computers/ubuntu').new()
		ubuntu.props.name = 'ubuntu'
		ubuntu.save()
		try:
			containers = self.udm.get('container/cn')
			container = containers.new()
			container.props.name = 'ubuntu'
			container.save()
			try:
				container.position = ubuntu.position
				with self.assertRaises(MoveError):
					container.save()
			finally:
				container.delete()
		finally:
			ubuntu.delete()

	def test_default_position(self):
		ubuntu = self.udm.get('computers/ubuntu').new()
		assert ubuntu.position == 'cn=computers,%s' % self.ucr_test['ldap/base']
		memberserver = self.udm.get('computers/memberserver').new()
		assert memberserver.position == 'cn=memberserver,cn=computers,%s' % self.ucr_test['ldap/base']
		slave = self.udm.get('computers/domaincontroller_slave').new()
		assert slave.position == 'cn=dc,cn=computers,%s' % self.ucr_test['ldap/base']
		backup = self.udm.get('computers/domaincontroller_backup').new()
		assert backup.position == 'cn=dc,cn=computers,%s' % self.ucr_test['ldap/base']
		master = self.udm.get('computers/domaincontroller_master').new()
		assert master.position == 'cn=dc,cn=computers,%s' % self.ucr_test['ldap/base']


if __name__ == '__main__':
	main(verbosity=2)
