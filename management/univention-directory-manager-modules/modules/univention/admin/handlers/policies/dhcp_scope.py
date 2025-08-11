# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for |DHCP| scope policies"""

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


class dhcp_scopeFixedAttributes(univention.admin.syntax.select):
    name = 'dhcp_scopeFixedAttributes'
    choices = [
        ('univentionDhcpUnknownClients', _('Unknown clients')),
        ('univentionDhcpBootp', _('BOOTP')),
        ('univentionDhcpBooting', _('Booting')),
        ('univentionDhcpDuplicates', _('Duplicates')),
        ('univentionDhcpDeclines', _('Declines')),
    ]


module = 'policies/dhcp_scope'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = "univentionPolicyDhcpScope"
policy_apply_to = ["dhcp/service", "dhcp/subnet", "dhcp/host", "dhcp/sharedsubnet", "dhcp/shared"]
policy_position_dn_prefix = "cn=scope,cn=dhcp"
policies_group = "dhcp"
childs = False
short_description = _('Policy: DHCP Allow/Deny')
object_name = _('DHCP Allow/Deny policy')
object_name_plural = _('DHCP Allow/Deny policies')
policy_short_description = _('Allow/Deny')
long_description = ''
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionPolicy', 'univentionPolicyDhcpScope'],
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
    'scopeUnknownClients': univention.admin.property(
        short_description=_('Unknown clients'),
        long_description=_('Dynamically assign addresses to unknown clients. Allowed by default. This option should not be used anymore.'),
        syntax=univention.admin.syntax.AllowDenyIgnore,
    ),
    'bootp': univention.admin.property(
        short_description=_('BOOTP'),
        long_description=_('Respond to BOOTP queries. Allowed by default.'),
        syntax=univention.admin.syntax.AllowDenyIgnore,
    ),
    'booting': univention.admin.property(
        short_description=_('Booting'),
        long_description=_('Respond to queries from a particular client. Has meaning only when it appears in a host declaration. Allowed by default.'),
        syntax=univention.admin.syntax.AllowDenyIgnore,
    ),
    'duplicates': univention.admin.property(
        short_description=_('Duplicates'),
        long_description=_('If a request is received from a client that matches the MAC address of a host declaration, any other leases matching that MAC address will be discarded by the server, if this is set to deny. Allowed by default. Setting this to deny violates the DHCP protocol.'),
        syntax=univention.admin.syntax.AllowDeny,
    ),
    'declines': univention.admin.property(
        short_description=_('Declines'),
        long_description=_("Honor DHCPDECLINE messages. deny/ignore will prevent malicious or buggy clients from completely exhausting the DHCP server's allocation pool."),
        syntax=univention.admin.syntax.AllowDenyIgnore,
    ),
}, **dict([
    requiredObjectClassesProperty(),
    prohibitedObjectClassesProperty(),
    fixedAttributesProperty(syntax=dhcp_scopeFixedAttributes),
    emptyAttributesProperty(syntax=dhcp_scopeFixedAttributes),
    ldapFilterProperty(),
]))

layout = [
    Tab(_('Allow/Deny'), _('Allow/Deny/Ignore statements'), layout=[
        Group(_('General DHCP allow/deny settings'), layout=[
            'name',
            ['scopeUnknownClients', 'bootp'],
            ['booting', 'duplicates'],
            'declines',
        ]),
    ]),
    policy_object_tab(),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('scopeUnknownClients', 'univentionDhcpUnknownClients', None, univention.admin.mapping.ListToString)
mapping.register('bootp', 'univentionDhcpBootp', None, univention.admin.mapping.ListToString)
mapping.register('booting', 'univentionDhcpBooting', None, univention.admin.mapping.ListToString)
mapping.register('duplicates', 'univentionDhcpDuplicates', None, univention.admin.mapping.ListToString)
mapping.register('declines', 'univentionDhcpDeclines', None, univention.admin.mapping.ListToString)
register_policy_mapping(mapping)


class object(univention.admin.handlers.simplePolicy):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
