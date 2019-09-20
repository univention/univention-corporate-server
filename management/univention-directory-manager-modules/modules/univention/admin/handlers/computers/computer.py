# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the computer objects
#
# Copyright 2004-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

import univention.admin.handlers.computers

translation = univention.admin.localization.translation('univention.admin.handlers.computers')
_ = translation.translate

module = 'computers/computer'
childmodules = []
for computer in univention.admin.handlers.computers.computers:
	childmodules.append(computer.module)

childs = 0
short_description = _('Computer')
object_name = _('Computer')
object_name_plural = _('Computers')
long_description = ''
operations = ['search']
virtual = 1
options = {
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.hostName,
		include_in_default_search=True,
		required=True,
		identifies=True
	),
	'dnsAlias': univention.admin.property(
		short_description=_('DNS alias'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
	),
	'mac': univention.admin.property(
		short_description=_('MAC address'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		include_in_default_search=True,
	),
	'ip': univention.admin.property(
		short_description=_('IP address'),
		long_description='',
		syntax=univention.admin.syntax.ipAddress,
		multivalue=True,
		include_in_default_search=True,
	),
	'inventoryNumber': univention.admin.property(
		short_description=_('Inventory number'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		include_in_default_search=True,
	),
	'fqdn': univention.admin.property(
		short_description='FQDN',
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
		may_change=False,
		dontsearch=True
	)
}

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('inventoryNumber', 'univentionInventoryNumber')
mapping.register('mac', 'macAddress')


class object(univention.admin.handlers.simpleLdap):
	module = module

	def open(self):
		super(object, self).open()
		if 'name' in self.info and 'domain' in self.info:
			# in syntax.py IComputer_FQDN key and label are '%(name)s.%(domain)s' for
			#   performance reasons. These statements and this fqdn over here have to
			#   be in sync.
			self['fqdn'] = '%s.%s' % (self['name'], self['domain'])


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):
	res = []
	for computer in univention.admin.handlers.computers.computers:
		res.extend(computer.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit))
	return res


def identify(dn, attr, canonical=0):
	pass
