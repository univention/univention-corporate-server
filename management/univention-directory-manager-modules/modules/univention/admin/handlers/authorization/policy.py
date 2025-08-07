# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for authorization policies"""

from __future__ import annotations

from logging import getLogger

import univention.admin.handlers
import univention.admin.localization
from univention.admin.layout import Group, Tab


log = getLogger('ADMIN')

translation = univention.admin.localization.translation('univention.admin.handlers.authorization')
_ = translation.translate

module = 'authorization/policy'
operations = ['add', 'edit', 'remove', 'search']
childs = False
default_containers = ['cn=authz,cn=univention']
short_description = _('Authorization Policy')
object_name = _('Authorization Policy')
object_name_plural = _('Authorization Policy')
long_description = ''


# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionAuthorizationPolicy'],
    ),
}

property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description=_('Name of this authorization policy'),
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
    ),
    'description': univention.admin.property(
        short_description=_('Description'),
        long_description='',
        syntax=univention.admin.syntax.string,
        size='Two',
    ),
    'roles': univention.admin.property(
        short_description=_('Roles'),
        long_description='',
        syntax=univention.admin.syntax.GuardianRole,
        multivalue=True,
        required=True,
        size='Two',
    ),
    'privileges': univention.admin.property(
        short_description=_('Privileges'),
        long_description=_('Grant access to privileges'),
        syntax=univention.admin.syntax.AuthorizationPrivileges,
        required=True,
        multivalue=True,
        size='Two',
    ),
}

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('Role selection'), layout=[
            ["name"],
            ["description"],
        ]),
        Group(_('Access Rights'), layout=[
            ["roles"],
            ["privileges"],
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('roles', 'univentionAuthorizationRole')
mapping.register('privileges', 'univentionAuthorizationTo')
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
