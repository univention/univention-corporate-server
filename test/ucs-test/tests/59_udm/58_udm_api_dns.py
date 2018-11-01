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
from univention.udm.exceptions import NoSuperordinate, CreateError, MoveError


ud.init('/var/log/univention/directory-manager-cmd.log', ud.FLUSH, 0)
ud.set_level(ud.ADMIN, ud.ALL)


PostalAddress = namedtuple('PostalAddress', ['street', 'zipcode', 'city'])


class TestUdmUsersBasic(TestCase):
	@classmethod
	def setUpClass(cls):
		cls.udm = UDM.admin().version(1)
		cls.ucr_test = UCSTestConfigRegistry()
		cls.ucr_test.load()

	def test_superordinate_and_duplicate(self):
		host_records = self.udm.get('dns/host_record')
		with self.assertRaises(NoSuperordinate):
			host_records.new()
		forward_zones = self.udm.get('dns/forward_zone')
		forward_zone = list(forward_zones.search())[0]
		host_record1 = host_records.new(forward_zone)
		assert host_record1.position == forward_zone.dn
		host_record1.props.name = 'x1'
		host_record1.save()
		try:
			host_record1_dup = host_records.new(forward_zone)
			host_record1_dup.props.name = 'x1'
			with self.assertRaises(CreateError):
				host_record1_dup.save()
		finally:
			host_record1.delete()

	def test_superordinate_and_move(self):
		host_records = self.udm.get('dns/host_record')
		with self.assertRaises(NoSuperordinate):
			host_records.new()
		forward_zones = self.udm.get('dns/forward_zone')
		forward_zone = list(forward_zones.search())[0]
		host_record2 = host_records.new(forward_zone.dn)
		host_record2.props.name = 'x2'
		host_record2.save()
		try:
			host_record2.position = self.ucr_test['ldap/base']
			with self.assertRaises(MoveError):
				host_record2.save()
		finally:
			host_record2.delete()


if __name__ == '__main__':
	main(verbosity=2)
