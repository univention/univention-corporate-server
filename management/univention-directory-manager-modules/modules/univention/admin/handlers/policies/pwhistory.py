# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for the password history policies"""

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


class pwhistoryFixedAttributes(univention.admin.syntax.select):
    name = 'pwhistoryFixedAttributes'
    choices = [
        ('univentionPWHistoryLen', _('History length')),
        ('univentionPWExpiryInterval', _('Password expiry interval')),
        ('univentionPWLength', _('Password length')),
    ]


module = 'policies/pwhistory'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = 'univentionPolicyPWHistory'
policy_apply_to = ['users/user', 'users/ldap']
policy_position_dn_prefix = 'cn=pwhistory,cn=users'
childs = False
short_description = _('Policy: Passwords')
object_name = _('Passwords policy')
object_name_plural = _('Passwords policies')
policy_short_description = _('Passwords')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionPolicy', 'univentionPolicyPWHistory'],
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
    'length': univention.admin.property(
        short_description=_('History length'),
        long_description=_('This number indicates after how many changes the user may reuse the old password again'),
        syntax=univention.admin.syntax.integer,
    ),
    'expiryInterval': univention.admin.property(
        short_description=_('Password expiry interval'),
        long_description=_('Number of days after which the password has to be changed'),
        syntax=univention.admin.syntax.integer,
    ),
    'pwLength': univention.admin.property(
        short_description=_('Password length'),
        long_description=_('Minimal amount of characters'),
        syntax=univention.admin.syntax.integer,
    ),
    'pwQualityCheck': univention.admin.property(
        short_description=_('Password quality check'),
        long_description=_('Enables/disables password quality checks for example dictionary entries'),
        syntax=univention.admin.syntax.TrueFalseUp,
    ),

}, **dict([
    requiredObjectClassesProperty(),
    prohibitedObjectClassesProperty(),
    fixedAttributesProperty(syntax=pwhistoryFixedAttributes),
    emptyAttributesProperty(syntax=pwhistoryFixedAttributes),
    ldapFilterProperty(),
]))

layout = [
    Tab(_('General'), _('Passwords'), layout=[
        Group(_('General passwords settings'), layout=[
            'name',
            'pwLength',
            'expiryInterval',
            'length',
            'pwQualityCheck',
        ]),
    ]),
    policy_object_tab(),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('length', 'univentionPWHistoryLen', None, univention.admin.mapping.ListToIntToString)
mapping.register('expiryInterval', 'univentionPWExpiryInterval', None, univention.admin.mapping.ListToIntToString)
mapping.register('pwLength', 'univentionPWLength', None, univention.admin.mapping.ListToIntToString)
mapping.register('pwQualityCheck', 'univentionPWQualityCheck', None, univention.admin.mapping.ListToString)
register_policy_mapping(mapping)
# fmt: on


class object(univention.admin.handlers.simplePolicy):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
