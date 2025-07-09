#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for the admin container policies"""

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


class adminFixedAttributes(univention.admin.syntax.select):
    name = 'adminFixedAttributes'
    choices = [
        ('univentionAdminListModules', _('List of Univention Directory Manager modules')),
    ]


module = 'policies/admin_container'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = 'univentionPolicyAdminContainerSettings'
policy_apply_to = []
policy_position_dn_prefix = "cn=container,cn=admin"

childs = False
short_description = _('Policy: Univention Directory Manager container settings')
object_name = _('Univention Directory Manager container settings policy')
object_name_plural = _('Univention Directory Manager container settings policies')
policy_short_description = _('Univention Directory Manager container settings')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionPolicy', 'univentionPolicyAdminContainerSettings'],
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
    'listModules': univention.admin.property(
        short_description=_('Available Univention Directory Manager modules'),
        long_description='',
        syntax=univention.admin.syntax.univentionAdminModules,
        multivalue=True,
    ),
}, **dict([
    requiredObjectClassesProperty(),
    prohibitedObjectClassesProperty(),
    fixedAttributesProperty(syntax=adminFixedAttributes),
    emptyAttributesProperty(syntax=adminFixedAttributes),
    ldapFilterProperty(),
]))

layout = [
    Tab(_('General'), _('Univention Directory Manager settings'), layout=[
        Group(_('General Univention Directory Manager container settings'), layout=[
            'name',
            'listModules',
        ]),
    ]),
    policy_object_tab(),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('listModules', 'univentionAdminListModules')
register_policy_mapping(mapping)
# fmt: on


class object(univention.admin.handlers.simplePolicy):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
