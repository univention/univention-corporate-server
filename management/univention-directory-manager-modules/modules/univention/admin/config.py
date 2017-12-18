# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  configuration basics
#
# Copyright 2004-2017 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

import univention.admin.modules
import univention.admin.uldap


class config:

	def __init__(self, host=''):
		base = univention.admin.uldap.getBaseDN(host)
		self.data = {
			'ldap/base': base,
			'ldap/base/dns': 'cn=dns,' + base,
			'ldap/base/dhcp': 'cn=dhcp,' + base
		}

	def __getitem__(self, key):
		return self.data[key]

	def __setitem__(self, key, value):
		self.data[key] = value

	def has_key(self, key):
		return key in self

	def __contains__(self, key):
		return key in self.data

	def items(self):
		return self.data.items()


def getDefaultContainer(lo, module):
	if isinstance(module, type('str')):
		if module == 'users/user':
			att = 'univentionUsersObject'
		elif module == 'groups/group':
			att = 'univentionGroupsObject'
		elif module == 'computers/windows':
			att = 'univentionComputersObject'
		elif module.startswith('dns/'):
			att = 'univentionDnsObject'
	else:
		module = univention.admin.modules.name(module)

		if module == 'users/user':
			att = 'univentionUsersObject'
		elif module == 'groups/group':
			att = 'univentionGroupsObject'
		elif module == 'computers/windows':
			att = 'univentionComputersObject'
		elif module.startswith('dns/'):
			att = 'univentionDnsObject'

	dn, attrs = lo.search(filter='objectClass=univentionDirectory', attr=[att], scope='domain', unique=True, required=True)[0]
	return attrs.get(att, [None])[0]


def getDefaultValue(lo, name, position=None):

	if name == 'group':
		att = 'univentionDefaultGroup'
	elif name == 'computerGroup':
		att = 'univentionDefaultComputerGroup'
	else:
		att = name

	if position:
		dn, attrs = lo.search(filter='objectClass=univentionDefault', attr=[att], base=position.getDomain(), scope='domain', unique=True, required=True)[0]
	else:
		dn, attrs = lo.search(filter='objectClass=univentionDefault', attr=[att], scope='domain', unique=True, required=True)[0]
	return attrs.get(att, [None])[0]
