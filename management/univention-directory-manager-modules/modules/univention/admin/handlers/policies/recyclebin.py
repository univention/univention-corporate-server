# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Policy defining recycle bin configuration"""

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


class recycleBinFixedAttributes(univention.admin.syntax.select):
    name = 'recycleBinFixedAttributes'
    choices = [
        ('univentionRecycleBinEnabled', _('Recycle bin enabled')),
        ('univentionRecycleBinUDMModules', _('UDM modules to recycle')),
        ('univentionRecycleBinProperties', _('Properties to store')),
        ('univentionRecycleBinRetentionTime', _('Retention time (days)')),
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
]
policy_position_dn_prefix = 'cn=recyclebin'

childs = False
short_description = _('Policy: Recycle Bin Configuration')
object_name = _('Recycle bin policy')
object_name_plural = _('Recycle bin policies')
policy_short_description = _('Defines recycle bin behavior for UDM objects')
long_description = _('This policy controls which UDM objects are moved to the recycle bin when deleted, which properties are stored, and how long they are retained.')

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
        long_description=_('Name of the recycle bin policy'),
        syntax=udm_syntax.policyName,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
    ),
    'enabled': univention.admin.property(
        short_description=_('Recycle bin enabled'),
        long_description=_('Enable or disable recycle bin for objects in this scope'),
        syntax=udm_syntax.TrueFalseUpper,
        default='TRUE',
    ),
    'udm_modules': univention.admin.property(
        short_description=_('UDM modules to recycle'),
        long_description=_('List of UDM module names whose objects should be recycled when deleted'),
        syntax=udm_syntax.string,
        multivalue=True,
        default=['users/user', 'groups/group', 'computers/*'],
    ),
    'properties': univention.admin.property(
        short_description=_('Properties to store'),
        long_description=_('List of property names to store in recycled objects (empty = all properties)'),
        syntax=udm_syntax.string,
        multivalue=True,
    ),
    'retention_time': univention.admin.property(
        short_description=_('Retention time (days)'),
        long_description=_('Number of days to keep objects in recycle bin (0 = indefinite)'),
        syntax=udm_syntax.integer,
        default='365',
    ),
}, **dict([
    requiredObjectClassesProperty(),
    prohibitedObjectClassesProperty(),
    fixedAttributesProperty(syntax=recycleBinFixedAttributes),
    emptyAttributesProperty(syntax=recycleBinFixedAttributes),
    ldapFilterProperty(),
]))

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('General recycle bin settings'), layout=[
            'name',
            'enabled',
            'retention_time',
        ]),
        Group(_('UDM configuration'), layout=[
            'udm_modules',
            'properties',
        ]),
    ]),
    policy_object_tab(),
]

mapping = udm_mapping.mapping()
mapping.register('name', 'cn', None, udm_mapping.ListToString)
mapping.register('enabled', 'univentionRecycleBinEnabled', None, udm_mapping.ListToString)
mapping.register('udm_modules', 'univentionRecycleBinUDMModules')
mapping.register('properties', 'univentionRecycleBinProperties')
mapping.register('retention_time', 'univentionRecycleBinRetentionTime', None, udm_mapping.ListToString)
register_policy_mapping(mapping)
# fmt: on


class object(simplePolicy):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
