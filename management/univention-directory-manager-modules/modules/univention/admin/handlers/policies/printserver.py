#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for the print server policies"""

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
from univention.admin.layout import Group, Tab
from univention.admin.policy import (
    emptyAttributesProperty, fixedAttributesProperty, ldapFilterProperty, policy_object_tab,
    prohibitedObjectClassesProperty, register_policy_mapping, requiredObjectClassesProperty,
)


translation = univention.admin.localization.translation('univention.admin.handlers.policies')
_ = translation.translate


class printServerFixedAttributes(univention.admin.syntax.select):
    name = 'updateFixedAttributes'
    choices = [
        ('univentionPrintServer', _('Print server')),
    ]


module = 'policies/printserver'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = 'univentionPolicyPrintServer'
policy_apply_to = ['computers/memberserver', 'computers/domaincontroller_backup', 'computers/domaincontroller_master', 'computers/domaincontroller_slave']
policy_position_dn_prefix = 'cn=printservers'

childs = False
short_description = _('Policy: Print server')
object_name = _('Print server policy')
object_name_plural = _('Print server policies')
policy_short_description = _('Print server')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionPolicy', 'univentionPolicyPrintServer'],
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
    'printServer': univention.admin.property(
        short_description=_('Print server'),
        long_description='',
        syntax=univention.admin.syntax.ServicePrint_FQDN,
        include_in_default_search=True,
    ),

}, **dict([
    requiredObjectClassesProperty(),
    prohibitedObjectClassesProperty(),
    fixedAttributesProperty(syntax=printServerFixedAttributes),
    emptyAttributesProperty(syntax=printServerFixedAttributes),
    ldapFilterProperty(),
]))

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('General print server settings'), layout=[
            'name',
            'printServer',
        ]),
    ]),
    policy_object_tab(),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('printServer', 'univentionPrintServer', None, univention.admin.mapping.ListToString)
register_policy_mapping(mapping)
# fmt: on


class object(univention.admin.handlers.simplePolicy):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
