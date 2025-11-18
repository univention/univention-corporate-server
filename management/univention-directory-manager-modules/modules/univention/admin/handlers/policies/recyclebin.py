# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Policy defining recyclebin configuration"""

import univention.admin.localization
import univention.admin.mapping as udm_mapping
import univention.admin.syntax as udm_syntax
from univention.admin.handlers import simplePolicy
from univention.admin.layout import Tab
from univention.admin.policy import (
    emptyAttributesProperty, fixedAttributesProperty, ldapFilterProperty, policy_object_tab,
    prohibitedObjectClassesProperty, register_policy_mapping, requiredObjectClassesProperty,
)


translation = univention.admin.localization.translation('univention.admin.handlers.policies')
_ = translation.translate


class recycleBinFixedAttributes(univention.admin.syntax.select):
    name = 'recycleBinFixedAttributes'
    choices = [
        ('univentionRecycleBinEnabled', _('Recyclebin enabled')),
        ('univentionRecycleBinUDMModules', _('UDM modules to recycle')),
        ('univentionRecycleBinRetentionDays', _('Retention days')),
    ]


module = 'policies/recyclebin'
operations = ('add', 'edit', 'remove', 'search')

policy_oc = 'univentionRecycleBinPolicy'
policy_apply_to = [
    'container/ou',
    'container/cn',
    'users/user',
    'groups/group',
    'computers/domaincontroller_master',
    'computers/domaincontroller_backup',
    'computers/domaincontroller_slave',
    'computers/memberserver',
    'computers/windows',
    'computers/linux',
    'computers/ubuntu',
    'computers/macos',
]  # TODO: automatically add all modules which support the recyclebin
policy_position_dn_prefix = 'cn=recyclebin'

childs = False
short_description = _('Policy: Recyclebin Configuration')
object_name = _('Recyclebin policy')
object_name_plural = _('Recyclebin policies')
policy_short_description = _('Defines recyclebin behavior for UDM objects')
long_description = _('This policy controls which UDM objects are moved to the recyclebin when deleted and how long they are retained.')

# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionPolicy', 'univentionRecycleBinPolicy'],
    ),
}

property_descriptions = dict({
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description=_('Name of the recyclebin policy'),
        syntax=udm_syntax.policyName,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
    ),
    'enabled': univention.admin.property(
        short_description=_('Recyclebin enabled'),
        long_description=_('Enable or disable recyclebin for objects in this scope'),
        syntax=udm_syntax.TrueFalseUp,
        default='TRUE',
    ),
    'udm_modules': univention.admin.property(
        short_description=_('UDM modules to recycle'),
        long_description=_('List of UDM module names whose objects should be recycled when deleted'),
        syntax=udm_syntax.RecycleBinSupportedModules,
        multivalue=True,
    ),
    'retention_days': univention.admin.property(
        short_description=_('Retention days'),
        long_description=_('Number of days to keep objects in recyclebin (0 = indefinite)'),
        syntax=udm_syntax.integer,
        default='180',
    ),
    'ignored_object_classes': univention.admin.property(
        short_description=_('Ignored object classes'),
        long_description=_('Objects having one of these object classes will not be moved to recyclebin.'),
        syntax=udm_syntax.ldapObjectClass,
    ),
}, **dict([
    requiredObjectClassesProperty(editable=False),
    prohibitedObjectClassesProperty(editable=False),
    fixedAttributesProperty(syntax=recycleBinFixedAttributes, editable=False),
    emptyAttributesProperty(syntax=recycleBinFixedAttributes, editable=False),
    ldapFilterProperty(editable=False),
]))

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        'name',
        'enabled',
        'retention_days',
        'udm_modules',
        'ignored_object_classes',
    ]),
    policy_object_tab(),
]

mapping = udm_mapping.mapping()
mapping.register('name', 'cn', None, udm_mapping.ListToString)
mapping.register('enabled', 'univentionRecycleBinEnabled', None, udm_mapping.ListToString)
mapping.register('udm_modules', 'univentionRecycleBinUDMModules')
mapping.register('retention_days', 'univentionRecycleBinRetentionDays', None, udm_mapping.ListToString)
mapping.register('ignored_object_classes', 'univentionRecycleBinIgnoredObjectClasses')
register_policy_mapping(mapping)
# fmt: on


class object(simplePolicy):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
