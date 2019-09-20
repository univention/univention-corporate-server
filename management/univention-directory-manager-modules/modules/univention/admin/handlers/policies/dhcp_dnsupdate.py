# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin policy for the DHCP dnsupdate settings
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

from univention.admin.layout import Tab, Group
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

from univention.admin.policy import (
	register_policy_mapping, policy_object_tab,
	requiredObjectClassesProperty, prohibitedObjectClassesProperty,
	fixedAttributesProperty, emptyAttributesProperty, ldapFilterProperty
)


translation = univention.admin.localization.translation('univention.admin.handlers.policies')
_ = translation.translate


class dhcp_dnsupdateFixedAttributes(univention.admin.syntax.select):
	name = 'dhcp_dnsupdateFixedAttributes'
	choices = [
		('univentionDhcpDdnsHostname', _('DDNS hostname')),
		('univentionDhcpDdnsDomainname', _('DDNS domain name')),
		('univentionDhcpDdnsRevDomainname', _('DDNS reverse domain name')),
		('univentionDhcpDdnsUpdates', _('DDNS updates')),
		('univentionDhcpDdnsDdnsUpdateStyle', _('DDNS update style')),
		('univentionDhcpDdnsDoForwardUpdates', _('DDNS forward update')),
		('univentionDhcpDdnsUpdateStaticLeases', _('Update static leases')),
		('univentionDhcpDdnsClientUpdates', _('Client updates'))
	]


module = 'policies/dhcp_dnsupdate'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = "univentionPolicyDhcpDnsUpdate"
policy_apply_to = ["dhcp/host", "dhcp/pool", "dhcp/service", "dhcp/subnet", "dhcp/sharedsubnet", "dhcp/shared"]
policy_position_dn_prefix = "cn=dnsupdate,cn=dhcp"
policies_group = "dhcp"
childs = 0
short_description = _('Policy: DHCP Dynamic DNS')
object_name = _('DHCP Dynamic DNS policy')
object_name_plural = _('DHCP Dynamic DNS policies')
policy_short_description = _('Dynamic DNS')
long_description = ''
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionPolicy', 'univentionPolicyDhcpDnsUpdate'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.policyName,
		include_in_default_search=True,
		required=True,
		may_change=False,
		identifies=True,
	),
	'ddnsHostname': univention.admin.property(
		short_description=_('DDNS hostname'),
		long_description=_("Hostname that will be used for the client's A and PTR records"),
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
	),
	'ddnsDomainname': univention.admin.property(
		short_description=_('DDNS domain name'),
		long_description=_("Domain name that will be appended to the client's hostname to form a fully-qualified domain-name (FQDN)"),
		syntax=univention.admin.syntax.string,
	),
	'ddnsRevDomainname': univention.admin.property(
		short_description=_('DDNS reverse domain name'),
		long_description=_("Domain name that will be appended to the client's hostname to produce a name for use in the client's PTR record"),
		syntax=univention.admin.syntax.string,
	),
	'ddnsUpdates': univention.admin.property(
		short_description=_('DDNS updates'),
		long_description=_("Attempt to do a DNS update when a DHCP lease is confirmed"),
		syntax=univention.admin.syntax.ddnsUpdates,
	),
	'ddnsUpdateStyle': univention.admin.property(
		short_description=_('DDNS update style'),
		long_description=_("Specify the DDNS Update Style to use for a DHCP Service"),
		syntax=univention.admin.syntax.ddnsUpdateStyle,
	),
	'ddnsDoForwardUpdate': univention.admin.property(
		short_description=_('DDNS forward update'),
		long_description=_("Attempt to update a DHCP client's A record when the client acquires or renews a lease"),
		syntax=univention.admin.syntax.TrueFalse,
	),
	'updateStaticLeases': univention.admin.property(
		short_description=_('Update static leases'),
		long_description=_("Do DNS updates for clients even if their IP addresses are assigned using fixed addresses"),
		syntax=univention.admin.syntax.TrueFalse,
	),
	'clientUpdates': univention.admin.property(
		short_description=_('Client updates'),
		long_description=_("Honor the client's intention to do its own update of its A record"),
		syntax=univention.admin.syntax.AllowDeny,
	),
}
property_descriptions.update(dict([
	requiredObjectClassesProperty(),
	prohibitedObjectClassesProperty(),
	fixedAttributesProperty(syntax=dhcp_dnsupdateFixedAttributes),
	emptyAttributesProperty(syntax=dhcp_dnsupdateFixedAttributes),
	ldapFilterProperty(),
]))

layout = [
	Tab(_('DNS Update'), _('Dynamic DNS update'), layout=[
		Group(_('General DHCP dynamic DNS settings'), layout=[
			'name',
			['ddnsDomainname', 'ddnsRevDomainname'],
			['ddnsUpdates', 'ddnsUpdateStyle'],
			['ddnsDoForwardUpdate', 'updateStaticLeases'],
			'clientUpdates'
		]),
	]),
	policy_object_tab()
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('ddnsHostname', 'univentionDhcpDdnsHostname', None, univention.admin.mapping.ListToString)
mapping.register('ddnsDomainname', 'univentionDhcpDdnsDomainname', None, univention.admin.mapping.ListToString)
mapping.register('ddnsRevDomainname', 'univentionDhcpDdnsRevDomainname', None, univention.admin.mapping.ListToString)
mapping.register('ddnsUpdates', 'univentionDhcpDdnsUpdates', None, univention.admin.mapping.ListToString)
mapping.register('ddnsUpdateStyle', 'univentionDhcpDdnsUpdateStyle', None, univention.admin.mapping.ListToString)
mapping.register('ddnsDoForwardUpdate', 'univentionDhcpDoForwardUpdates', None, univention.admin.mapping.ListToString)
mapping.register('updateStaticLeases', 'univentionDhcpUpdateStaticLeases', None, univention.admin.mapping.ListToString)
mapping.register('clientUpdates', 'univentionDhcpClientUpdates', None, univention.admin.mapping.ListToString)
register_policy_mapping(mapping)


class object(univention.admin.handlers.simplePolicy):
	module = module


lookup = object.lookup
identify = object.identify
