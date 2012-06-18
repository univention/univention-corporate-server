# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin policy for the DHCP scope
#
# Copyright 2004-2012 Univention GmbH
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
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.policies')
_=translation.translate

class dhcp_scopeFixedAttributes(univention.admin.syntax.select):
	name='dhcp_scopeFixedAttributes'
	choices=[
		('univentionDhcpUnknownClients',_('Unknown clients')),
		('univentionDhcpBootp',_('BOOTP')),
		('univentionDhcpBooting',_('Booting')),
		('univentionDhcpDuplicates',_('Duplicates')),
		('univentionDhcpDeclines',_('Declines'))
		]

module='policies/dhcp_scope'
operations=['add','edit','remove','search']

policy_oc="univentionPolicyDhcpScope"
policy_apply_to=["dhcp/service", "dhcp/subnet", "dhcp/host", "dhcp/sharedsubnet", "dhcp/shared"]
policy_position_dn_prefix="cn=scope,cn=dhcp"
policies_group="dhcp"
usewizard=1
childs=0
short_description=_('Policy: DHCP Allow/Deny')
policy_short_description=_('Allow/Deny')
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
			may_change=0,
			identifies=1,
		),
	'scopeUnknownClients': univention.admin.property(
			short_description=_('Unknown clients'),
			long_description=_('Dynamically assign addresses to unknown clients. Allowed by default. This option should not be used anymore.'),
			syntax=univention.admin.syntax.AllowDenyIgnore,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'bootp': univention.admin.property(
			short_description=_('BOOTP'),
			long_description=_('Respond to BOOTP queries. Allowed by default.'),
			syntax=univention.admin.syntax.AllowDenyIgnore,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'booting': univention.admin.property(
			short_description=_('Booting'),
			long_description=_('Respond to queries from a particular client. Has meaning only when it appears in a host declaration. Allowed by default.'),
			syntax=univention.admin.syntax.AllowDenyIgnore,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'duplicates': univention.admin.property(
			short_description=_('Duplicates'),
			long_description=_('If a request is received from a client that matches the MAC address of a host declaration, any other leases matching that MAC address will be discarded by the server, if this is set to deny. Allowed by default. Setting this to deny violates the DHCP protocol.'),
			syntax=univention.admin.syntax.AllowDeny,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'declines': univention.admin.property(
			short_description=_('Declines'),
			long_description=_("Honor DHCPDECLINE messages. deny/ignore will prevent malicious or buggy clients from completely exhausting the DHCP server's allocation pool."),
			syntax=univention.admin.syntax.AllowDenyIgnore,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'requiredObjectClasses': univention.admin.property(
			short_description=_('Required object classes'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'prohibitedObjectClasses': univention.admin.property(
			short_description=_('Excluded object classes'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'fixedAttributes': univention.admin.property(
			short_description=_('Fixed attributes'),
			long_description='',
			syntax=dhcp_scopeFixedAttributes,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'emptyAttributes': univention.admin.property(
			short_description=_('Empty attributes'),
			long_description='',
			syntax=dhcp_scopeFixedAttributes,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
}

layout = [
	Tab(_('Allow/Deny'), _('Allow/Deny/Ignore statements'), layout = [
		Group( _( 'General' ), layout = [
			'name',
			[ 'scopeUnknownClients', 'bootp' ],
			[ 'booting','duplicates' ],
			'declines'
		] ),
	] ),
	Tab(_('Object'),_('Object'), advanced = True, layout = [
		[ 'requiredObjectClasses' , 'prohibitedObjectClasses' ],
		[ 'fixedAttributes', 'emptyAttributes' ]
	] ),
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('scopeUnknownClients', 'univentionDhcpUnknownClients', None, univention.admin.mapping.ListToString)
mapping.register('bootp', 'univentionDhcpBootp', None, univention.admin.mapping.ListToString)
mapping.register('booting', 'univentionDhcpBooting', None, univention.admin.mapping.ListToString)
mapping.register('duplicates', 'univentionDhcpDuplicates', None, univention.admin.mapping.ListToString)
mapping.register('declines', 'univentionDhcpDeclines', None, univention.admin.mapping.ListToString)

mapping.register('requiredObjectClasses', 'requiredObjectClasses')
mapping.register('prohibitedObjectClasses', 'prohibitedObjectClasses')
mapping.register('fixedAttributes', 'fixedAttributes')
mapping.register('emptyAttributes', 'emptyAttributes')

class object(univention.admin.handlers.simplePolicy):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global mapping
		global property_descriptions

		self.mapping=mapping
		self.descriptions=property_descriptions

		univention.admin.handlers.simplePolicy.__init__(self, co, lo, position, dn, superordinate, attributes )

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_addlist(self):
		return [
			('objectClass', ['top', 'univentionPolicy', 'univentionPolicyDhcpScope'])
		]

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionPolicyDhcpScope'),
		])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	try:
		for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
			res.append( object( co, lo, None, dn, attributes = attrs ) )
	except:
		pass
	return res

def identify(dn, attr, canonical=0):

	return 'univentionPolicyDhcpScope' in attr.get('objectClass', [])
