# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for |DHCP| routing policies"""

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


class dhcp_routingFixedAttributes(univention.admin.syntax.select):
    name = 'dhcp_routingFixedAttributes'
    choices = [
        ('univentionDhcpRouters', _('Routers')),
    ]


module = 'policies/dhcp_routing'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = 'univentionPolicyDhcpRouting'
policy_apply_to = ['dhcp/host', 'dhcp/pool', 'dhcp/service', 'dhcp/subnet', 'dhcp/sharedsubnet', 'dhcp/shared']
policy_position_dn_prefix = 'cn=routing,cn=dhcp'
policies_group = 'dhcp'
childs = False
short_description = _('Policy: DHCP routing')
object_name = _('DHCP routing policy')
object_name_plural = _('DHCP routing policies')
policy_short_description = _('Routing')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionPolicy', 'univentionPolicyDhcpRouting'],
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
        ldap_attribute='cn',
    ),
    'routers': univention.admin.property(
        short_description=_('Routers'),
        long_description='',
        syntax=univention.admin.syntax.hostOrIP,
        multivalue=True,
        ldap_attribute='univentionDhcpRouters',
    ),
}, **dict([
    requiredObjectClassesProperty(),
    prohibitedObjectClassesProperty(),
    fixedAttributesProperty(syntax=dhcp_routingFixedAttributes),
    emptyAttributesProperty(syntax=dhcp_routingFixedAttributes),
    ldapFilterProperty(),
]))

layout = [
    Tab(_('General'), _('DHCP routing'), layout=[
        Group(_('General DHCP routing settings'), layout=[
            'name',
            'routers',
        ]),
    ]),
    policy_object_tab(),
]

mapping = univention.admin.mapping.mapping()
mapping.from_properties(property_descriptions)
register_policy_mapping(mapping)
# fmt: on


class object(univention.admin.handlers.simplePolicy):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
