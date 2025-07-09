#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for |DHCP| lease time setting policies"""

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.syntax
from univention.admin.layout import Group, Tab
from univention.admin.policy import (
    emptyAttributesProperty, fixedAttributesProperty, ldapFilterProperty, policy_object_tab,
    prohibitedObjectClassesProperty, register_policy_mapping, requiredObjectClassesProperty,
)


translation = univention.admin.localization.translation('univention.admin.handlers.policies')
_ = translation.translate


class dhcp_leasetimeFixedAttributes(univention.admin.syntax.select):
    name = 'dhcp_leasetimeFixedAttributes'
    choices = [
        ('univentionDhcpLeaseTimeDefault', _('Default lease time')),
        ('univentionDhcpLeaseTimeMax', _('Maximum lease time')),
        ('univentionDhcpLeaseTimeMin', _('Minimum lease time')),
    ]


module = 'policies/dhcp_leasetime'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = 'univentionPolicyDhcpLeaseTime'
policy_apply_to = ['dhcp/host', 'dhcp/pool', 'dhcp/service', 'dhcp/subnet', 'dhcp/sharedsubnet', 'dhcp/shared']
policy_position_dn_prefix = 'cn=leasetime,cn=dhcp'
policies_group = 'dhcp'
childs = False
short_description = _('Policy: DHCP lease time')
object_name = _('DHCP lease time policy')
object_name_plural = _('DHCP lease time policies')
policy_short_description = _('Lease time')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionPolicy', 'univentionPolicyDhcpLeaseTime'],
    ),
}
property_descriptions = dict({
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
}, **dict([
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
    policy_object_tab(),
]


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('lease_time_default', 'univentionDhcpLeaseTimeDefault', univention.admin.mapping.mapUNIX_TimeInterval, univention.admin.mapping.unmapUNIX_TimeInterval)
mapping.register('lease_time_max', 'univentionDhcpLeaseTimeMax', univention.admin.mapping.mapUNIX_TimeInterval, univention.admin.mapping.unmapUNIX_TimeInterval)
mapping.register('lease_time_min', 'univentionDhcpLeaseTimeMin', univention.admin.mapping.mapUNIX_TimeInterval, univention.admin.mapping.unmapUNIX_TimeInterval)
register_policy_mapping(mapping)
# fmt: on


class object(univention.admin.handlers.simplePolicy):
    module = module

    def __setitem__(self, key, value):
        if not value or not value[0]:
            return  # FIXME: why?
        if key in ('lease_time_min', 'lease_time_max', 'lease_time_default') and value and value[0] == '':
            return
        univention.admin.handlers.simplePolicy.__setitem__(self, key, value)


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
