# SPDX-FileCopyrightText: 2011-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""admin module: policy defining access restriction for UMC"""

import univention.admin.localization
import univention.admin.mapping as udm_mapping
import univention.admin.syntax as udm_syntax
from univention.admin.handlers import simplePolicy
from univention.admin.layout import Group, Tab
from univention.admin.policy import (
    emptyAttributesProperty, fixedAttributesProperty, ldapFilterProperty, policy_object_tab,
    prohibitedObjectClassesProperty, register_policy_mapping, requiredObjectClassesProperty,
)


translation = univention.admin.localization.translation('univention.admin.handlers.policies')
_ = translation.translate


class umcFixedAttributes(udm_syntax.select):
    choices = (
        ('umcPolicyGrantedOperationSet', _('Allowed UMC operation sets')),
    )


module = 'policies/umc'
operations = ('add', 'edit', 'remove', 'search')

policy_oc = 'umcPolicy'
policy_apply_to = [
    'users/user',
    'users/ldap',
    'groups/group',
    'computers/domaincontroller_master',
    'computers/domaincontroller_backup',
    'computers/domaincontroller_slave',
    'computers/memberserver',
]
policy_position_dn_prefix = 'cn=UMC'

childs = False
short_description = _('Policy: UMC')
object_name = _('UMC policy')
object_name_plural = _('UMC policies')
policy_short_description = _('Defines a set of allowed UMC operations')
long_description = ''

# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionPolicy', 'umcPolicy'],
    ),
}
property_descriptions = dict({
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description='',
        syntax=udm_syntax.policyName,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
    ),
    'allow': univention.admin.property(
        short_description=_('List of allowed UMC operation sets'),
        long_description='',
        syntax=udm_syntax.UMC_OperationSet,
        multivalue=True,
    ),
}, **dict([
    requiredObjectClassesProperty(),
    prohibitedObjectClassesProperty(),
    fixedAttributesProperty(syntax=umcFixedAttributes),
    emptyAttributesProperty(syntax=umcFixedAttributes),
    ldapFilterProperty(),
]))

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('General UMC settings'), layout=[
            'name',
            'allow',
        ]),
    ]),
    policy_object_tab(),
]

mapping = udm_mapping.mapping()
mapping.register('name', 'cn', None, udm_mapping.ListToString)
mapping.register('allow', 'umcPolicyGrantedOperationSet')
register_policy_mapping(mapping)
# fmt: on


class object(simplePolicy):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
