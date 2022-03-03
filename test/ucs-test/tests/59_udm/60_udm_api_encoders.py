#!/usr/share/ucs-test/runner pytest-3
# -*- coding: utf-8 -*-
## desc: Test UDM API for users/user module
## exposure: dangerous
## roles: [domaincontroller_master]
## tags: [udm_api, skip_admember]
## packages: [python3-univention-directory-manager]
## bugs: [51184]

from unittest import TestCase, main

import univention.debug as ud
from univention.testing.strings import random_username
from univention.udm import UDM
from univention.udm.exceptions import DeleteError

ud.init('/var/log/univention/directory-manager-cmd.log', ud.FLUSH, 0)
ud.set_level(ud.ADMIN, ud.ALL)


class TestEncoders(TestCase):
	user_objects = []

	@classmethod
	def setUpClass(cls):
		cls.udm = UDM.admin().version(2)

	@classmethod
	def tearDownClass(cls):
		for obj in cls.user_objects:
			try:
				obj.delete()
				print('tearDownClass(): Deleted {!r}.'.format(obj))
			except DeleteError:
				print('tearDownClass(): Already deleted: {!r}.'.format(obj))

	def test_dn_list_property_encoder(self):
		user_mod = self.udm.get('users/user')
		obj = user_mod.new()
		self.user_objects.append(obj)
		attrs = {
			'firstname': random_username(),
			'lastname': random_username(),
			'username': random_username(),
			'password': random_username(),
		}
		print('Creating user with attrs: {!r}'.format(attrs))
		for k, v in attrs.items():
			setattr(obj.props, k, v)
		obj.save()
		assert obj.props.secretary.objs == []

		obj2 = user_mod.new()
		self.user_objects.append(obj2)
		attrs = {
			'firstname': random_username(),
			'lastname': random_username(),
			'username': random_username(),
			'password': random_username(),
		}
		print('Creating user with attrs: {!r}'.format(attrs))
		for k, v in attrs.items():
			setattr(obj2.props, k, v)
		obj2.save()

		obj.props.secretary.append(obj2.dn)
		obj.save()
		assert [o.dn for o in obj.props.secretary.objs] == [obj2.dn]


if __name__ == '__main__':
	main()
