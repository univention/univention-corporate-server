# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  configuration basics
#
# Copyright (C) 2004-2009 Univention GmbH
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

import univention.admin.modules
import univention.admin.uldap

class config:
	def __init__(self, host=''):
		base=univention.admin.uldap.getBaseDN(host)
		self.data={
			'ldap/base': base,
			'ldap/base/dns': 'cn=dns,'+base,
			'ldap/base/dhcp': 'cn=dhcp,'+base
		}
	def __getitem__(self, key):
		return self.data[key]
	def __setitem__(self, key, value):
		self.data[key]=value
	def has_key(self, key):
		return self.data.has_key(key)
	def items(self):
		return self.data.items()


def getDefaultContainer(lo, module):
	if type(module) == type('str'):
		if module == 'users/user':
			att='univentionUsersObject'
		elif module == 'groups/group':
			att='univentionGroupsObject'
		elif module == 'computers/windows':
			att='univentionComputersObject'
		elif module.startswith('dns/'):
			att='univentionDnsObject'
	else:
		module=univention.admin.modules.name(module)

		if module == 'users/user':
			att='univentionUsersObject'
		elif module == 'groups/group':
			att='univentionGroupsObject'
		elif module == 'computers/windows':
			att='univentionComputersObject'
		elif module.startswith('dns/'):
			att='univentionDnsObject'

	dn, attrs=lo.search(filter='objectClass=univentionDirectory', attr=[att], scope='domain', unique=1, required=1)[0]
	return attrs.get(att, [None])[0]


def getDefaultValue(lo, name, position=None):

	if name == 'group':
		att='univentionDefaultGroup'
	elif name == 'computerGroup':
		att='univentionDefaultComputerGroup'
	else:
		att=name


	if position:
		dn, attrs=lo.search(filter='objectClass=univentionDefault', attr=[att], base=position.getDomain(), scope='domain', unique=1, required=1)[0]
	else:
		dn, attrs=lo.search(filter='objectClass=univentionDefault', attr=[att], scope='domain', unique=1, required=1)[0]
	return attrs.get(att, [None])[0]
