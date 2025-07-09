# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for the |DHCP| |DNS| update settings policies"""

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
        ('univentionDhcpDdnsClientUpdates', _('Client updates')),
    ]


module = 'policies/dhcp_dnsupdate'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = 'univentionPolicyDhcpDnsUpdate'
policy_apply_to = ['dhcp/host', 'dhcp/pool', 'dhcp/service', 'dhcp/subnet', 'dhcp/sharedsubnet', 'dhcp/shared']
policy_position_dn_prefix = 'cn=dnsupdate,cn=dhcp'
policies_group = 'dhcp'
childs = False
short_description = _('Policy: DHCP Dynamic DNS')
object_name = _('DHCP Dynamic DNS policy')
object_name_plural = _('DHCP Dynamic DNS policies')
policy_short_description = _('Dynamic DNS')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionPolicy', 'univentionPolicyDhcpDnsUpdate'],
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
}, **dict([
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
            'clientUpdates',
        ]),
    ]),
    policy_object_tab(),
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
# fmt: on


class object(univention.admin.handlers.simplePolicy):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
