# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for authorization policies"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

import univention.admin.handlers
import univention.admin.localization
from univention.admin.layout import Group, Tab


if TYPE_CHECKING:
    from collections.abc import Sequence

log = getLogger('ADMIN')

translation = univention.admin.localization.translation('univention.admin.handlers.authorization')
_ = translation.translate

module = 'authorization/privilege'
operations = ['add', 'edit', 'remove', 'search']
childs = False
short_description = _('Authorization Privilege')
object_name = _('Authorization Privilege')
object_name_plural = _('Authorization Privilege')
long_description = ''


# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionAuthorizationPrivilege'],
    ),
}

property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description=_('Name of this privilege'),
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
    'objecttype': univention.admin.property(
        short_description=_('Object Type'),
        long_description=_('Grant access to object type'),
        syntax=univention.admin.syntax.univentionAdminModules,
        required=True,
    ),
    'actions': univention.admin.property(
        short_description=_('Action permissions'),
        long_description=_('Grant actions.'),
        syntax=univention.admin.syntax.AuthorizationActions,
        multivalue=True,
        required=True,
    ),
    'properties': univention.admin.property(
        short_description=_('Property permissions'),
        long_description=_('Grant specified permissions to properties under the given restrictions'),
        syntax=univention.admin.syntax.AuthorizationProperties,
        multivalue=True,
    ),
    'position': univention.admin.property(
        short_description=_('Position with scope'),
        long_description='',
        syntax=univention.admin.syntax.AuthorizationScopePosition,
    ),
    'condition': univention.admin.property(
        short_description=_('Condition'),
        long_description=_('Further restriction where this policy applies to'),
        syntax=univention.admin.syntax.string,
    ),
}

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('Role selection'), layout=[
            ["name"],
            ["description"],
        ]),
        Group(_('Access Rights'), layout=[
            ["objecttype", "position"],
            ["condition"],
            ["actions"],
            "properties",
        ]),
    ]),
]
# fmt: on


def mapProperties(old: Sequence[str], encoding: Sequence[str] = ()) -> list[bytes]:
    """
    Map complex

    >>> mapProperties([["a", "b", "c"]])
    [b'a b c']
    """
    new = []
    for i in old:
        new.append(' '.join(i).encode(*encoding))
    return new


def unmapProperties(old: Sequence[bytes], encoding: Sequence[str] = ()) -> list[list[str]]:
    """
    Expand complex

    >>> unmapProperties([b'foo'])
    [['foo', ' ', ' ']]
    >>> unmapProperties([b'foo bar baz'])
    [['foo', 'bar', 'baz']]
    """
    new = []
    for i in old:
        if b' ' in i:
            new.append(i.decode(*encoding).split(' '))
        else:
            new.append([i.decode(*encoding), ' ', ' '])
    return new


def mapPosition(old: Sequence[str], encoding: Sequence[str] = ()) -> list[bytes]:
    """
    Map complex

    >>> mapPosition(["base", "dc=example,dc=org"])
    [b'base dc=example,dc=org']
    """
    new = []
    for i in [old]:
        new.append(' '.join(i).encode(*encoding))
    return new


def unmapPosition(old: Sequence[bytes], encoding: Sequence[str] = ()) -> list[list[str]]:
    """
    Expand complex

    >>> unmapPosition([b'base'])
    ['base', ' ']
    >>> unmapPosition([b'base dc=example,dc=org'])
    ['base', 'dc=example,dc=org']
    """
    new = []
    for i in old:
        if b' ' in i:
            new.append(i.decode(*encoding).split(' '))
        else:
            new.append([i.decode(*encoding), ' '])
    return new[0]


# fmt: off
mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('objecttype', 'univentionAuthorizationObjectType', None, univention.admin.mapping.ListToString)
mapping.register('actions', 'univentionAuthorizationGrantsAction')
mapping.register('properties', 'univentionAuthorizationGrantsProperties', mapProperties, unmapProperties)
mapping.register('position', 'univentionAuthorizationPosition', mapPosition, unmapPosition)
mapping.register('condition', 'univentionAuthorizationCondition', None, univention.admin.mapping.ListToString)
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
