#!/usr/share/ucs-test/runner /usr/bin/py.test
# -*- coding: utf-8 -*-
## desc: Test UDM APIs module caching
## exposure: dangerous
## roles: [domaincontroller_master]
## tags: [udm_api]
## packages: [python-univention-directory-manager]
## bugs: [47316]

from unittest import main, TestCase
from univention.udm import UDM


class TestUdmModuleCaching(TestCase):
	def test_caching(self):
		assert UDM.admin().version(0).get('users/user') is UDM.admin().version(0).get('users/user')
		assert UDM.admin().version(0).get('users/user') is not UDM.admin().version(1).get('users/user')
		assert UDM.admin().version(1).get('users/user') is UDM.admin().version(1).get('users/user')
		assert UDM.admin().version(0).get('users/user') is not UDM.admin().version(0).get('groups/group')
		assert UDM.admin().version(0).get('users/user') is not UDM.machine().version(0).get('users/user')


if __name__ == '__main__':
	main(verbosity=2)
