# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin policy for the DHCP leasetime settings
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


class dhcp_leasetimeFixedAttributes(univention.admin.syntax.select):
	name = 'dhcp_leasetimeFixedAttributes'
	choices = [
		('univentionDhcpLeaseTimeDefault', _('Default lease time')),
		('univentionDhcpLeaseTimeMax', _('Maximum lease time')),
		('univentionDhcpLeaseTimeMin', _('Minimum lease time'))
	]


module = 'policies/dhcp_leasetime'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = "univentionPolicyDhcpLeaseTime"
policy_apply_to = ["dhcp/host", "dhcp/pool", "dhcp/service", "dhcp/subnet", "dhcp/sharedsubnet", "dhcp/shared"]
policy_position_dn_prefix = "cn=leasetime,cn=dhcp"
policies_group = "dhcp"
childs = 0
short_description = _('Policy: DHCP lease time')
object_name = _('DHCP lease time policy')
object_name_plural = _('DHCP lease time policies')
policy_short_description = _('Lease time')
long_description = ''
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionPolicy', 'univentionPolicyDhcpLeaseTime'],
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
	'lease_time_default': univention.admin.property(
		short_description=_('Default lease time'),
		long_description=_('Lease time used if the client does not request a specific expiration time'),
		syntax=univention.admin.syntax.UNIX_TimeInterval,
	),
	'lease_time_max': univention.admin.property(
		short_description=_('Maximum lease time'),
		long_description=_('Maximum lease time that the server will accept if asked for'),
		syntax=univention.admin.syntax.UNIX_TimeInterval,
	),
	'lease_time_min': univention.admin.property(
		short_description=_('Minimum lease time'),
		long_description=_('Minimum granted lease time'),
		syntax=univention.admin.syntax.UNIX_TimeInterval,
	),
}
property_descriptions.update(dict([
	requiredObjectClassesProperty(),
	prohibitedObjectClassesProperty(),
	fixedAttributesProperty(syntax=dhcp_leasetimeFixedAttributes),
	emptyAttributesProperty(syntax=dhcp_leasetimeFixedAttributes),
	ldapFilterProperty(),
]))

layout = [
	Tab(_('Lease Time'), _('DHCP lease time'), layout=[
		Group(_('General DHCP lease time settings'), layout=[
			'name',
			'lease_time_default',
			'lease_time_min',
			'lease_time_max',
		]),
	]),
	policy_object_tab()
]


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('lease_time_default', 'univentionDhcpLeaseTimeDefault', univention.admin.mapping.mapUNIX_TimeInterval, univention.admin.mapping.unmapUNIX_TimeInterval)
mapping.register('lease_time_max', 'univentionDhcpLeaseTimeMax', univention.admin.mapping.mapUNIX_TimeInterval, univention.admin.mapping.unmapUNIX_TimeInterval)
mapping.register('lease_time_min', 'univentionDhcpLeaseTimeMin', univention.admin.mapping.mapUNIX_TimeInterval, univention.admin.mapping.unmapUNIX_TimeInterval)
register_policy_mapping(mapping)


class object(univention.admin.handlers.simplePolicy):
	module = module

	def __setitem__(self, key, value):
		if value and value[0]:
			if not ((key == 'lease_time_min' or key == 'lease_time_max' or key == 'lease_time_default') and value[0] == ''):
				univention.admin.handlers.simplePolicy.__setitem__(self, key, value)


lookup = object.lookup
identify = object.identify
