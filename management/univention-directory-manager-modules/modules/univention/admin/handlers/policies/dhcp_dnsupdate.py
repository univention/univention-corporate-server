# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin policy for the DHCP dnsupdate settings
#
# Copyright 2004-2011 Univention GmbH
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

class dhcp_dnsupdateFixedAttributes(univention.admin.syntax.select):
	name='dhcp_dnsupdateFixedAttributes'
	choices=[
		('univentionDhcpDdnsHostname',_('DDNS hostname')),
		('univentionDhcpDdnsDomainname',_('DDNS domain name')),
		('univentionDhcpDdnsRevDomainname',_('DDNS reverse domain name')),
		('univentionDhcpDdnsUpdates',_('DDNS updates')),
		('univentionDhcpDdnsDdnsUpdateStyle',_('DDNS update style')),
		('univentionDhcpDdnsDoForwardUpdates',_('DDNS forward update')),
		('univentionDhcpDdnsUpdateStaticLeases',_('Update static leases')),
		('univentionDhcpDdnsClientUpdates',_('Client updates'))
		]

module='policies/dhcp_dnsupdate'
operations=['add','edit','remove','search']

policy_oc="univentionPolicyDhcpDnsUpdate"
policy_apply_to=["dhcp/host", "dhcp/pool", "dhcp/service", "dhcp/subnet", "dhcp/sharedsubnet", "dhcp/shared"]
policy_position_dn_prefix="cn=dnsupdate,cn=dhcp"
policies_group="dhcp"
usewizard=1
childs=0
short_description=_('Policy: DHCP Dynamic DNS')
policy_short_description=_('Dynamic DNS')
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
	'ddnsHostname': univention.admin.property(
			short_description=_('DDNS hostname'),
			long_description=_("Hostname that will be used for the client's A and PTR records"),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'ddnsDomainname': univention.admin.property(
			short_description=_('DDNS domain name'),
			long_description=_("Domain name that will be appended to the client's hostname to form a fully-qualified domain-name (FQDN)"),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'ddnsRevDomainname': univention.admin.property(
			short_description=_('DDNS reverse domain name'),
			long_description=_("Domain name that will be appended to the client's hostname to produce a name for use in the client's PTR record"),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'ddnsUpdates': univention.admin.property(
			short_description=_('DDNS updates'),
			long_description=_("Attempt to do a DNS update when a DHCP lease is confirmed"),
			syntax=univention.admin.syntax.ddnsUpdates,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'ddnsUpdateStyle': univention.admin.property(
			short_description=_('DDNS update style'),
			long_description=_("Specify the DDNS Update Style to use for a DHCP Service"),
			syntax=univention.admin.syntax.ddnsUpdateStyle,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'ddnsDoForwardUpdate': univention.admin.property(
			short_description=_('DDNS forward update'),
			long_description=_("Attempt to update a DHCP client's A record when the client acquires or renews a lease"),
			syntax=univention.admin.syntax.TrueFalse,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'updateStaticLeases': univention.admin.property(
			short_description=_('Update static leases'),
			long_description=_("Do DNS updates for clients even their IP addresses are assigned using fixed addresses"),
			syntax=univention.admin.syntax.TrueFalse,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'clientUpdates': univention.admin.property(
			short_description=_('Client updates'),
			long_description=_("Honor the client's intention to do its own update of its A record"),
			syntax=univention.admin.syntax.AllowDeny,
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
			syntax=dhcp_dnsupdateFixedAttributes,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'emptyAttributes': univention.admin.property(
			short_description=_('Empty attributes'),
			long_description='',
			syntax=dhcp_dnsupdateFixedAttributes,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
}

layout = [
	Tab(_('DNS Update'), _('Dynamic DNS update'), layout = [
		Group( _( 'General' ), layout = [
			'name',
			[ 'ddnsDomainname', 'ddnsRevDomainname' ],
			[ 'ddnsUpdates', 'ddnsUpdateStyle' ],
			[ 'ddnsDoForwardUpdate', 'updateStaticLeases' ],
			'clientUpdates'
		] ),
	] ),
	Tab(_('Object'),_('Object'), advanced = True, layout = [
		[ 'requiredObjectClasses' , 'prohibitedObjectClasses' ],
		[ 'fixedAttributes', 'emptyAttributes' ]
	] ),
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('ddnsHostname', 'univentionDhcpDdnsHostname', None, univention.admin.mapping.ListToString)
mapping.register('ddnsDomainname', 'univentionDhcpDdnsDomainname', None, univention.admin.mapping.ListToString)
mapping.register('ddnsRevDomainname', 'univentionDhcpDdnsRevDomainname', None, univention.admin.mapping.ListToString)
mapping.register('ddnsUpdates', 'univentionDhcpDdnsUpdates', None, univention.admin.mapping.ListToString)
mapping.register('ddnsUpdateStyle', 'univentionDhcpDdnsUpdateStyle', None, univention.admin.mapping.ListToString)
mapping.register('ddnsDoForwardUpdate', 'univentionDhcpDoForwardUpdates', None, univention.admin.mapping.ListToString)
mapping.register('updateStaticLeases', 'univentionDhcpUpdateStaticLeases', None, univention.admin.mapping.ListToString)
mapping.register('clientUpdates', 'univentionDhcpClientUpdates', None, univention.admin.mapping.ListToString)

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
			('objectClass', ['top', 'univentionPolicy', 'univentionPolicyDhcpDnsUpdate'])
		]

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionPolicyDhcpDnsUpdate'),
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

	return 'univentionPolicyDhcpDnsUpdate' in attr.get('objectClass', [])
