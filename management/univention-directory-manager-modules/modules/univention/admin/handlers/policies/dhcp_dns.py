#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for the |DHCP| |DNS| settings policies"""

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


class dhcp_dnsFixedAttributes(univention.admin.syntax.select):
    name = 'dhcp_dnsFixedAttributes'
    choices = [
        ('univentionDhcpDomainName', _('Domain name')),
        ('univentionDhcpDomainNameServers', _('Domain name servers')),
    ]


module = 'policies/dhcp_dns'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = "univentionPolicyDhcpDns"
policy_apply_to = ["dhcp/host", "dhcp/pool", "dhcp/service", "dhcp/subnet", "dhcp/sharedsubnet", "dhcp/shared"]
policy_position_dn_prefix = "cn=dns,cn=dhcp"
policies_group = "dhcp"
childs = False
short_description = _('Policy: DHCP DNS')
object_name = _('DHCP DNS policy')
object_name_plural = _('DHCP DNS policies')
policy_short_description = _('DNS')
long_description = ''
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionPolicy', 'univentionPolicyDhcpDns'],
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
    'domain_name': univention.admin.property(
        short_description=_('Domain name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
    ),
    'domain_name_servers': univention.admin.property(
        short_description=_('Domain name servers'),
        long_description='',
        syntax=univention.admin.syntax.string,
        multivalue=True,
    ),
}, **dict([
    requiredObjectClassesProperty(),
    prohibitedObjectClassesProperty(),
    fixedAttributesProperty(syntax=dhcp_dnsFixedAttributes),
    emptyAttributesProperty(syntax=dhcp_dnsFixedAttributes),
    ldapFilterProperty(),
]))

layout = [
    Tab(_('General'), _('Basic DNS settings'), layout=[
        Group(_('General DHCP DNS settings'), layout=[
            'name',
            ['domain_name', 'domain_name_servers'],
        ]),
    ]),
    policy_object_tab(),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('domain_name', 'univentionDhcpDomainName', None, univention.admin.mapping.ListToString)
mapping.register('domain_name_servers', 'univentionDhcpDomainNameServers')
register_policy_mapping(mapping)


class object(univention.admin.handlers.simplePolicy):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
