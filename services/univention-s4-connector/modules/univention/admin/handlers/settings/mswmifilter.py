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

import ldap

import univention.admin.syntax
import univention.admin.handlers
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.settings.mswmifilter')
_ = translation.translate

module = 'settings/mswmifilter'
operations = ['add', 'edit', 'remove', 'search', 'move', 'subtree_move']
childs = True
short_description = _('Settings: MS WMI Filter')
long_description = ''
options = {
	'default': univention.admin.option(
		short_description='',
		default=True,
		objectClasses=['msWMISom', 'top']
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		required=True,
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
	'id': univention.admin.property(
		short_description=_('MS WMI ID'),
		long_description='',
		syntax=univention.admin.syntax.string,
		identifies=True
	),
	'author': univention.admin.property(
		short_description=_('MS WMI Author'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'creationDate': univention.admin.property(
		short_description=_('MS WMI Creation Date'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'changeDate': univention.admin.property(
		short_description=_('MS WMI Change Date'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'parm1': univention.admin.property(
		short_description=_('MS WMI Parameter1'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'parm2': univention.admin.property(
		short_description=_('MS WMI Parameter2'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'parm3': univention.admin.property(
		short_description=_('MS WMI Parameter3'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'parm4': univention.admin.property(
		short_description=_('MS WMI Parameter4'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'flags1': univention.admin.property(
		short_description=_('MS WMI Flags1'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'flags2': univention.admin.property(
		short_description=_('MS WMI Flags2'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'flags3': univention.admin.property(
		short_description=_('MS WMI Flags3'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'flags4': univention.admin.property(
		short_description=_('MS WMI Flags4'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'sourceOrganization': univention.admin.property(
		short_description=_('MS WMI Source Organization'),
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
	Tab(_('WMI filter'), _('MS WMI filter'), advanced=True, layout=[
		Group(_('WMI filter'), layout=[
			['id'],
			['author'],
			['creationDate'],
			['changeDate'],
			['parm1'],
			['parm2'],
			['parm3'],
			['parm4'],
			#['flags1'],
			#['flags2'],
			#['flags3'],
			#['flags4'],
			#['sourceOrganization'],
		]),
	])
]

mapping = univention.admin.mapping.mapping()
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('displayName', 'displayName', None, univention.admin.mapping.ListToString)
mapping.register('name', 'msWMIName', None, univention.admin.mapping.ListToString)
mapping.register('id', 'msWMIID', None, univention.admin.mapping.ListToString)
mapping.register('author', 'msWMIAuthor', None, univention.admin.mapping.ListToString)
mapping.register('creationDate', 'msWMICreationDate', None, univention.admin.mapping.ListToString)
mapping.register('changeDate', 'msWMIChangeDate', None, univention.admin.mapping.ListToString)
mapping.register('parm1', 'msWMIParm1', None, univention.admin.mapping.ListToString)
mapping.register('parm2', 'msWMIParm2', None, univention.admin.mapping.ListToString)
mapping.register('parm3', 'msWMIParm3', None, univention.admin.mapping.ListToString)
mapping.register('parm4', 'msWMIParm4', None, univention.admin.mapping.ListToString)
mapping.register('flags1', 'msWMIintFlags1', None, univention.admin.mapping.ListToString)
mapping.register('flags2', 'msWMIintFlags2', None, univention.admin.mapping.ListToString)
mapping.register('flags3', 'msWMIintFlags3', None, univention.admin.mapping.ListToString)
mapping.register('flags4', 'msWMIintFlags4', None, univention.admin.mapping.ListToString)
mapping.register('sourceOrganization', 'msWMISourceOrganization', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_dn(self):
		dn = ldap.dn.str2dn(super(object, self)._ldap_dn())
		dn[0] = [('cn', dn[0][0][1], dn[0][0][2])]
		return ldap.dn.dn2str(dn)

	def _ldap_pre_modify(self):
		if self.hasChanged('id'):
			self.move(self._ldap_dn())


try:
	identify = object.identify
except AttributeError:  # FIXME: remove module into UDM-core or drop backwards compatibility
	# UCS < 4.4-0-errata102
	def identify(dn, attr, canonical=False):
		return 'msWMISom' in attr.get('objectClass', [])


try:
	lookup = object.lookup
except AttributeError:  # FIXME: remove module into UDM-core or drop backwards compatibility
	# UCS < 4.2-2 errata206
	def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):
		import univention.admin.filter
		filter = univention.admin.filter.conjunction('&', [
			univention.admin.filter.expression('objectClass', 'msWMISom'),
		])

		if filter_s:
			filter_p = univention.admin.filter.parse(filter_s)
			univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
			filter.expressions.append(filter_p)

		return [
			object(co, lo, None, dn, attributes=attrs)
			for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit)
		]
