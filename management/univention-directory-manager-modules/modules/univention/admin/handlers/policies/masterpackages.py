#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for the Primary or Backup Directory Node packages policies"""

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


class masterPackagesFixedAttributes(univention.admin.syntax.select):
    name = 'masterPackagesFixedAttributes'
    choices = [
        ('univentionMasterPackages', _('Package installation list')),
        ('univentionMasterPackagesRemove', _('Package removal list')),
    ]


module = 'policies/masterpackages'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = 'univentionPolicyPackagesMaster'
policy_apply_to = ["computers/domaincontroller_master", "computers/domaincontroller_backup"]
policy_position_dn_prefix = "cn=packages,cn=update"

childs = False
short_description = _('Policy: Packages for Primary/Backup Nodes')
object_name = _('Primary/Backup Node packages policy')
object_name_plural = _('Primary/Backup Node packages policies')
policy_short_description = _('Packages for Primary/Backup Nodes')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionPolicy', 'univentionPolicyPackagesMaster'],
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
    'masterPackages': univention.admin.property(
        short_description=_('Package installation list'),
        long_description='',
        syntax=univention.admin.syntax.Packages,
        multivalue=True,
    ),
    'masterPackagesRemove': univention.admin.property(
        short_description=_('Package removal list'),
        long_description='',
        syntax=univention.admin.syntax.PackagesRemove,
        multivalue=True,
    ),

}, **dict([
    requiredObjectClassesProperty(),
    prohibitedObjectClassesProperty(),
    fixedAttributesProperty(syntax=masterPackagesFixedAttributes),
    emptyAttributesProperty(syntax=masterPackagesFixedAttributes),
    ldapFilterProperty(),
]))

layout = [
    Tab(_('General'), policy_short_description, layout=[
        Group(_('General Primary/Backup Node packages settings'), layout=[
            'name',
            'masterPackages',
            'masterPackagesRemove',
        ]),
    ]),
    policy_object_tab(),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('masterPackages', 'univentionMasterPackages')
mapping.register('masterPackagesRemove', 'univentionMasterPackagesRemove')
register_policy_mapping(mapping)
# fmt: on


class object(univention.admin.handlers.simplePolicy):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
