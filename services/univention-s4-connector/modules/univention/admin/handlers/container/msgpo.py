# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  UDM module for MS GPOs
#
# Copyright 2012-2019 Univention GmbH
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

from univention.admin.layout import Tab, Group
import univention.admin.syntax
import univention.admin.handlers
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.container.msgpo')
_ = translation.translate

module = 'container/msgpo'
operations = ['add', 'edit', 'remove', 'search', 'move', 'subtree_move']
childs = 1
short_description = _('Container: MS Group Policy')
long_description = ''
options = {
	'default': univention.admin.option(
		short_description='',
		default=True,
		objectClasses=['msGPOContainer', 'top']
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		required=True,
		identifies=True
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'displayName': univention.admin.property(
		short_description=_('Display name'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'msGPOFlags': univention.admin.property(
		short_description=_('MS Group Policy Flags'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'msGPOVersionNumber': univention.admin.property(
		short_description=_('MS Group Policy Version Number'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'msGPOSystemFlags': univention.admin.property(
		short_description=_('MS Group Policy System Flags'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'msGPOFunctionalityVersion': univention.admin.property(
		short_description=_('MS Group Policy Functionality Version'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'msGPOFileSysPath': univention.admin.property(
		short_description=_('MS Group Policy File Sys Path'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'msGPOUserExtensionNames': univention.admin.property(
		short_description=_('MS Group Policy User Extension Names'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'msGPOMachineExtensionNames': univention.admin.property(
		short_description=_('MS Group Policy Machine Extension Names'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'msGPOWQLFilter': univention.admin.property(
		short_description=_('MS Group Policy WQL Filter'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'msNTSecurityDescriptor': univention.admin.property(
		short_description=_('MS NT Security Descriptor'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('General'), layout=[
			["name", "description"],
			["displayName"],
		]),
	]),
	Tab(_('GPO settings'), _('MS GPO settings'), advanced=True, layout=[
		Group(_('GPO settings'), layout=[
			['msGPOFlags'],
			['msGPOVersionNumber'],
			['msGPOSystemFlags'],
			['msGPOFunctionalityVersion'],
			['msGPOFileSysPath'],
			['msGPOWQLFilter'],
			['msGPOUserExtensionNames'],
			['msGPOMachineExtensionNames'],
		]),
	])
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('displayName', 'displayName', None, univention.admin.mapping.ListToString)
mapping.register('msGPOFlags', 'msGPOFlags', None, univention.admin.mapping.ListToString)
mapping.register('msGPOVersionNumber', 'msGPOVersionNumber', None, univention.admin.mapping.ListToString)
mapping.register('msGPOSystemFlags', 'msGPOSystemFlags', None, univention.admin.mapping.ListToString)
mapping.register('msGPOFunctionalityVersion', 'msGPOFunctionalityVersion', None, univention.admin.mapping.ListToString)
mapping.register('msGPOFileSysPath', 'msGPOFileSysPath', None, univention.admin.mapping.ListToString)
mapping.register('msGPOWQLFilter', 'msGPOWQLFilter', None, univention.admin.mapping.ListToString)
mapping.register('msGPOUserExtensionNames', 'msGPOUserExtensionNames', None, univention.admin.mapping.ListToString)
mapping.register('msGPOMachineExtensionNames', 'msGPOMachineExtensionNames', None, univention.admin.mapping.ListToString)
mapping.register('msNTSecurityDescriptor', 'msNTSecurityDescriptor', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_pre_modify(self):
		if self.hasChanged('name'):
			self.move(self._ldap_dn())


try:
	identify = object.identify
except AttributeError:  # FIXME: remove module into UDM-core or drop backwards compatibility
	# UCS < 4.4-0-errata102
	def identify(dn, attr, canonical=False):
		return 'msGPOContainer' in attr.get('objectClass', [])

try:
	lookup = object.lookup
except AttributeError:  # FIXME: remove module into UDM-core or drop backwards compatibility
	# UCS < 4.2-2 errata206
	def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):
		import univention.admin.filter
		filter = univention.admin.filter.conjunction('&', [
			univention.admin.filter.expression('objectClass', 'msGPOContainer'),
		])

		if filter_s:
			filter_p = univention.admin.filter.parse(filter_s)
			univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
			filter.expressions.append(filter_p)

		return [
			object(co, lo, None, dn, attributes=attrs)
			for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit)
		]
