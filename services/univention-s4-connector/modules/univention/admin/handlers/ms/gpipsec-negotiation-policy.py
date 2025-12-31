#
# Univention S4 Connector
#  UDM module for MS IPsec policy
#
# SPDX-FileCopyrightText: 2019-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import univention.admin.handlers
import univention.admin.localization
import univention.admin.syntax
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.ms')
_ = translation.translate

module = 'ms/gpipsec-negotiation-policy'
operations = ['add', 'edit', 'remove', 'search', 'move', 'subtree_move']
childs = True
short_description = _('MS IPsec policy: Negotiation Policy')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['ipsecNegotiationPolicy', 'top'],
    ),
}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        required=True,
        identifies=True,
    ),
    'description': univention.admin.property(
        short_description=_('Description'),
        long_description='',
        syntax=univention.admin.syntax.string,
        size='Two',
    ),
    'ipsecOwnersReference': univention.admin.property(
        short_description=_('IPsec Owners reference'),
        long_description='',
        multivalue=True,
        syntax=univention.admin.syntax.string,  # ipsecOwner,
    ),
    'ipsecName': univention.admin.property(
        short_description=_('IPsec Name'),
        long_description='',
        syntax=univention.admin.syntax.string,  # ipsecName,
    ),
    'ipsecID': univention.admin.property(
        short_description=_('IPsec ID'),
        long_description='',
        syntax=univention.admin.syntax.string,  # ipsecID,
    ),
    'ipsecDataType': univention.admin.property(
        short_description=_('IPsec Data Type'),
        long_description='',
        syntax=univention.admin.syntax.integer,
    ),
    'ipsecData': univention.admin.property(
        short_description=_('IPsec Data'),
        long_description='',
        syntax=univention.admin.syntax.TextArea,
    ),
    'iPSECNegotiationPolicyType': univention.admin.property(
        short_description=_('IPsec Negotiation Policy type'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
    'iPSECNegotiationPolicyAction': univention.admin.property(
        short_description=_('IPsec Negotiation Policy action'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
}

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('General'), layout=[
            "name",
            "description",
            'ipsecOwnersReference',
            'ipsecName',
            'ipsecID',
            'ipsecDataType',
            'ipsecData',
            'iPSECNegotiationPolicyType',
            'iPSECNegotiationPolicyAction',
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('ipsecOwnersReference', 'ipsecOwnersReference')
mapping.register('ipsecName', 'ipsecName', None, univention.admin.mapping.ListToString)
mapping.register('ipsecID', 'ipsecID', None, univention.admin.mapping.ListToString)
mapping.register('ipsecDataType', 'ipsecDataType', None, univention.admin.mapping.ListToString)
mapping.register('ipsecData', 'ipsecData', univention.admin.mapping.mapBase64, univention.admin.mapping.unmapBase64)
mapping.register('iPSECNegotiationPolicyType', 'iPSECNegotiationPolicyType', None, univention.admin.mapping.ListToString)
mapping.register('iPSECNegotiationPolicyAction', 'iPSECNegotiationPolicyAction', None, univention.admin.mapping.ListToString)
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module

    def _ldap_pre_modify(self):
        if self.hasChanged('name'):
            self.move(self._ldap_dn())


identify = object.identify
lookup = object.lookup
