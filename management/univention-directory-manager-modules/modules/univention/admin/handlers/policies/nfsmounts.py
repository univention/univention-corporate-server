# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for |NFS| mounts policies"""

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


class ldapServerFixedAttributes(univention.admin.syntax.select):
    name = 'updateFixedAttributes'
    choices = [
        ('univentionNFSMounts', _('Mount NFS shares')),
    ]


module = 'policies/nfsmounts'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = 'univentionPolicyNFSMounts'
policy_apply_to = ['computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave', 'computers/memberserver']
policy_position_dn_prefix = 'cn=nfsmounts'

childs = False
short_description = _('Policy: NFS mounts')
object_name = _('NFS mounts policy')
object_name_plural = _('NFS mounts policies')
policy_short_description = _('NFS mounts')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionPolicy', 'univentionPolicyNFSMounts'],
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
    'nfsMounts': univention.admin.property(
        short_description=_('NFS shares to mount'),
        long_description='',
        syntax=univention.admin.syntax.nfsMounts,
        multivalue=True,
        ldap_attribute='univentionNFSMounts',
        map=mapMounts,
        unmap=unmapMounts,
    ),

}, **dict([
    requiredObjectClassesProperty(),
    prohibitedObjectClassesProperty(),
    fixedAttributesProperty(syntax=ldapServerFixedAttributes),
    emptyAttributesProperty(syntax=ldapServerFixedAttributes),
    ldapFilterProperty(),
]))

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('General NFS mounts settings'), layout=[
            'name',
            'nfsMounts',
        ]),
    ]),
    policy_object_tab(),
]
# fmt: on


def unmapMounts(old, encoding=()):
    return [x.decode(*encoding).split(' ') for x in old]


def mapMounts(old, encoding=()):
    return [' '.join(x).encode(*encoding) for x in old]


# fmt: off
mapping = univention.admin.mapping.mapping()
mapping.from_properties(property_descriptions)
register_policy_mapping(mapping)
# fmt: on


class object(univention.admin.handlers.simplePolicy):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
