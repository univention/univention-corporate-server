# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  UDM module for ms-Print-ConnectionPolicy
#
# Copyright 2012-2015 Univention GmbH
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

translation=univention.admin.localization.translation('univention.admin.handlers.settings.msprintconnectionpolicy')
_=translation.translate

module='settings/msprintconnectionpolicy'
operations=['add','edit','remove','search','move','subtree_move']
childs=1
short_description=_('Settings: MS Print Connection Policy')
long_description=''
options={
}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=1
		),
	'description': univention.admin.property(
			short_description=_('Description'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'displayName': univention.admin.property(
			short_description=_('Display name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'msPrintAttributes': univention.admin.property(
			short_description=_('Print-Attributes'),
			long_description=_('A bitmask of printer attributes.'),
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=1
		),
	'msPrinterName': univention.admin.property(
			short_description=_('Printer-Name'),
			long_description=_('The display name of an attached printer.'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'msPrintServerName': univention.admin.property(
			short_description=_('Server-Name'),
			long_description=_('The name of a server.'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'msPrintUNCName': univention.admin.property(
			short_description=_('UNC-Name'),
			long_description=_('The universal naming convention name for shared volumes and printers.'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
}

layout = [
	Tab(_('General'),_('Basic settings'), layout = [
		[ 'name' ],
		[ 'description' ],
		[ 'displayName' ],
	] ),
	Tab(_('ms-Print-ConnectionPolicy'), advanced = True, layout = [
		[ 'msPrintAttributes' ],
		[ 'msPrinterName' ],
		[ 'msPrintServerName' ],
		[ 'msPrintUNCName' ],
	] )
]

mapping=univention.admin.mapping.mapping()
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('displayName', 'displayName', None, univention.admin.mapping.ListToString)
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('msPrintAttributes', 'msPrintAttributes', None, univention.admin.mapping.ListToString)
mapping.register('msPrinterName', 'msPrinterName',  None, univention.admin.mapping.ListToString)
mapping.register('msPrintServerName', 'msPrintServerName',  None, univention.admin.mapping.ListToString)
mapping.register('msPrintUNCName', 'msPrintUNCName',  None, univention.admin.mapping.ListToString)

class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global mapping
		global property_descriptions

		self.mapping=mapping
		self.descriptions=property_descriptions
		self.default_dn=''

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes = attributes )

		self.save()

	def _ldap_pre_create(self):
		self.dn='cn=%s,%s' % (mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_pre_modify(self):
		if self.hasChanged('name'):
			newdn = string.replace(self.dn, 'cn=%s,' % self.oldinfo['name'], 'cn=%s,' % self.info['name'], 1)
			self.move(newdn)

	def _ldap_addlist(self):
		return [
			('objectClass', ['top', 'msPrintConnectionPolicy'])
		]

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'msPrintConnectionPolicy'),
		])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append( object( co, lo, None, dn, attributes = attrs ) )
	return res

def identify(dn, attr, canonical=0):

	return 'msPrintConnectionPolicy' in attr.get('objectClass', [])
