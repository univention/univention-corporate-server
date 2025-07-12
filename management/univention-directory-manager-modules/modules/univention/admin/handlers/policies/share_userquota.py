# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for the share userquota policies"""

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


class shareUserQuotaFixedAttributes(univention.admin.syntax.select):
    name = 'shareUserQuotaFixedAttributes'
    choices = [
        ('univentionQuotaSoftLimitSpace', _('Soft limit')),
        ('univentionQuotaHardLimitSpace', _('Hard limit')),
        ('univentionQuotaSoftLimitInodes', _('Soft limit (Files)')),
        ('univentionQuotaHardLimitInodes', _('Hard limit (Files)')),
        ('univentionQuotaReapplyEveryLogin', _('Reapply settings on every login')),
    ]


module = 'policies/share_userquota'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = 'univentionPolicyShareUserQuota'
policy_apply_to = ['shares/share']
policy_position_dn_prefix = 'cn=userquota,cn=shares'

childs = False
short_description = _('Policy: User quota')
object_name = _('User quota policy')
object_name_plural = _('User quota policies')
policy_short_description = _('User quota')
long_description = _('Default quota for each user on a share')
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionPolicy', 'univentionPolicyShareUserQuota'],
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
    'softLimitSpace': univention.admin.property(
        short_description=_('Soft limit'),
        long_description=_('Soft limit. If exceeded users can be warned. Values may be entered with one of the following units as postfix: B (default), kB, MB, GB'),
        syntax=univention.admin.syntax.filesize,
        ldap_attribute='univentionQuotaSoftLimitSpace',
    ),
    'hardLimitSpace': univention.admin.property(
        short_description=_('Hard limit'),
        long_description=_('Hard limit. Can not be exceeded. Values may be entered with one of the following units as postfix: B (default), kB, MB, GB'),
        syntax=univention.admin.syntax.filesize,
        ldap_attribute='univentionQuotaHardLimitSpace',
    ),
    'softLimitInodes': univention.admin.property(
        short_description=_('Soft limit (Files)'),
        long_description=_('Soft limit. If exceeded users can be warned.'),
        syntax=univention.admin.syntax.integer,
        ldap_attribute='univentionQuotaSoftLimitInodes',
    ),
    'hardLimitInodes': univention.admin.property(
        short_description=_('Hard limit (Files)'),
        long_description=_('Hard limit. Can not be exceeded.'),
        syntax=univention.admin.syntax.integer,
        ldap_attribute='univentionQuotaHardLimitInodes',
    ),
    'reapplyeverylogin': univention.admin.property(
        short_description=_('Reapply settings on every login'),
        long_description=_('Reapply the mountpoint specific user quota policies on each user login. If not set, the initially configured quota settings will not be overwritten.'),
        syntax=univention.admin.syntax.TrueFalseUp,
        default="FALSE",
        ldap_attribute='univentionQuotaReapplyEveryLogin',
    ),

}, **dict([
    requiredObjectClassesProperty(),
    prohibitedObjectClassesProperty(),
    fixedAttributesProperty(syntax=shareUserQuotaFixedAttributes),
    emptyAttributesProperty(syntax=shareUserQuotaFixedAttributes),
    ldapFilterProperty(),
]))

layout = [
    Tab(_('General'), _('Quota'), layout=[
        Group(_('General user quota settings'), layout=[
            'name',
            ['softLimitSpace', 'hardLimitSpace'],
            ['softLimitInodes', 'hardLimitInodes'],
            ['reapplyeverylogin'],
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
