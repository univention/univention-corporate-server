# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for the Replica Directory Node packages policies"""

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


class slavePackagesFixedAttributes(univention.admin.syntax.select):
    name = 'slavePackagesFixedAttributes'
    choices = [
        ('univentionSlavePackages', _('Package installation list')),
        ('univentionSlavePackagesRemove', _('Package removal list')),
    ]


module = 'policies/slavepackages'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = 'univentionPolicyPackagesSlave'
policy_apply_to = ['computers/domaincontroller_slave']
policy_position_dn_prefix = 'cn=packages,cn=update'

childs = False
short_description = _('Policy: Packages for Replica Nodes')
object_name = _('Replica Node packages policy')
object_name_plural = _('Replica Node packages policies')
policy_short_description = _('Packages for Replica Nodes')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionPolicy', 'univentionPolicyPackagesSlave'],
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
    'slavePackages': univention.admin.property(
        short_description=_('Package installation list'),
        long_description='',
        syntax=univention.admin.syntax.Packages,
        multivalue=True,
        ldap_attribute='univentionSlavePackages',
    ),
    'slavePackagesRemove': univention.admin.property(
        short_description=_('Package removal list'),
        long_description='',
        syntax=univention.admin.syntax.PackagesRemove,
        multivalue=True,
        ldap_attribute='univentionSlavePackagesRemove',
    ),

}, **dict([
    requiredObjectClassesProperty(),
    prohibitedObjectClassesProperty(),
    fixedAttributesProperty(syntax=slavePackagesFixedAttributes),
    emptyAttributesProperty(syntax=slavePackagesFixedAttributes),
    ldapFilterProperty(),
]))

layout = [
    Tab(_('General'), policy_short_description, layout=[
        Group(_('General Replica Node packages settings'), layout=[
            'name',
            'slavePackages',
            'slavePackagesRemove',
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
