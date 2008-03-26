# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: policies/dhcp_netbios tests
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


from GenericTest import GenericTestCase


class PolicyDhcpNetbiosTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'policies/dhcp_netbios'
		super(PolicyDhcpNetbiosTestCase,
		      self).__init__(*args, **kwargs)

	def setUp(self):
		super(PolicyDhcpNetbiosTestCase, self).setUp()
		servers = ['mooh', 'gulli', 'ooohm']
		self.createProperties = {
			'requiredObjectClasses': 'univentionHost',
			'prohibitedObjectClasses': 'posixAccount',
			'fixedAttributes': 'univentionDhcpNetbiosNameServers',
			'netbios_scope': 'watawa',
			'netbios_node_type': '1',
			'netbios_name_servers': {'append': servers[:2]}
			}
		self.modifyProperties = {
			'requiredObjectClasses': 'posixAccount',
			'prohibitedObjectClasses': 'univentionHost',
			'fixedAttributes': 'univentionDhcpNetbiosScope',
			'netbios_scope': 'tawata',
			'netbios_node_type': '4',
			'netbios_name_servers': {'append': servers[2:],
						 'remove': servers[:1]}
			}
		self.name = 'testdhcpnetbiospolicy'


def suite():
	import sys, unittest
	suite = unittest.TestSuite()
	suite.addTest(PolicyDhcpNetbiosTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
