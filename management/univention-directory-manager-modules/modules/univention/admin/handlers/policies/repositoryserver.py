#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for the repository servers policies"""

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
        ('univentionRepositoryServer', _('Repository server')),
    ]


module = 'policies/repositoryserver'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = 'univentionPolicyRepositoryServer'
policy_apply_to = ["computers/domaincontroller_master", "computers/domaincontroller_backup", "computers/domaincontroller_slave", "computers/memberserver"]
policy_position_dn_prefix = "cn=repository,cn=update"

childs = False
short_description = _('Policy: Repository server')
object_name = _('Repository server policy')
object_name_plural = _('Repository server policies')
policy_short_description = _('Repository server')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionPolicy', 'univentionPolicyRepositoryServer'],
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
    'repositoryServer': univention.admin.property(
        short_description=_('Repository server'),
        long_description='',
        syntax=univention.admin.syntax.UCS_Server,
        include_in_default_search=True,
    ),

}, **dict([
    requiredObjectClassesProperty(),
    prohibitedObjectClassesProperty(),
    fixedAttributesProperty(syntax=ldapServerFixedAttributes),
    emptyAttributesProperty(syntax=ldapServerFixedAttributes),
    ldapFilterProperty(),
]))

layout = [
    Tab(_('General'), _('Update'), layout=[
        Group(_('General repository server settings'), layout=[
            'name',
            'repositoryServer',
        ]),
    ]),
    policy_object_tab(),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('repositoryServer', 'univentionRepositoryServer', None, univention.admin.mapping.ListToString)
register_policy_mapping(mapping)
# fmt: on


class object(univention.admin.handlers.simplePolicy):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
