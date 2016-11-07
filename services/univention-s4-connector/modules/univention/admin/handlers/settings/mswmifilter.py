# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  UDM module for MS GPOs
#
# Copyright 2012-2016 Univention GmbH
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

from univention.admin.layout import Tab, Group
import univention.admin.uldap
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import string

translation = univention.admin.localization.translation('univention.admin.handlers.settings.mswmifilter')
_ = translation.translate

module = 'settings/mswmifilter'
operations = ['add', 'edit', 'remove', 'search', 'move', 'subtree_move']
childs = 1
short_description = _('Settings: MS WMI Filter')
long_description = ''
options = {
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=True,
		may_change=True,
		identifies=True
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'displayName': univention.admin.property(
		short_description=_('Display name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'id': univention.admin.property(
		short_description=_('MS WMI ID'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=True
	),
	'author': univention.admin.property(
		short_description=_('MS WMI Author'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'creationDate': univention.admin.property(
		short_description=_('MS WMI Creation Date'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'changeDate': univention.admin.property(
		short_description=_('MS WMI Change Date'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'parm1': univention.admin.property(
		short_description=_('MS WMI Parameter1'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'parm2': univention.admin.property(
		short_description=_('MS WMI Parameter2'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'parm3': univention.admin.property(
		short_description=_('MS WMI Parameter3'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'parm4': univention.admin.property(
		short_description=_('MS WMI Parameter4'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'flags1': univention.admin.property(
		short_description=_('MS WMI Flags1'),
		long_description='',
		syntax=univention.admin.syntax.integer,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'flags2': univention.admin.property(
		short_description=_('MS WMI Flags2'),
		long_description='',
		syntax=univention.admin.syntax.integer,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'flags3': univention.admin.property(
		short_description=_('MS WMI Flags3'),
		long_description='',
		syntax=univention.admin.syntax.integer,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'flags4': univention.admin.property(
		short_description=_('MS WMI Flags4'),
		long_description='',
		syntax=univention.admin.syntax.integer,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'sourceOrganization': univention.admin.property(
		short_description=_('MS WMI Source Organization'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
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
			#			[ 'flags1' ],
			#			[ 'flags2' ],
			#			[ 'flags3' ],
			#			[ 'flags4' ],
			#			[ 'sourceOrganization' ],
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

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes=[]):
		global mapping
		global property_descriptions

		self.mapping = mapping
		self.descriptions = property_descriptions
		self.default_dn = ''

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes=attributes)

		self.save()

	def _ldap_pre_create(self):
		self.dn = 'cn=%s,%s' % (mapping.mapValue('id', self.info['id']), self.position.getDn())

	def _ldap_pre_modify(self):
		if self.hasChanged('id'):
			newdn = string.replace(self.dn, 'cn=%s,' % self.oldinfo['id'], 'cn=%s,' % self.info['id'], 1)
			self.move(newdn)

	def _ldap_addlist(self):
		return [
			('objectClass', ['top', 'msWMISom'])
		]


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):

	filter = univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'msWMISom'),
	])

	if filter_s:
		filter_p = univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res = []
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn, attributes=attrs))
	return res


def identify(dn, attr, canonical=0):

	return 'msWMISom' in attr.get('objectClass', [])
