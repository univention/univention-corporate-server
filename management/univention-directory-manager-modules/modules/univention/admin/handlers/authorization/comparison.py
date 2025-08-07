# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for authorization policies"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

import univention.admin.handlers
import univention.admin.localization
import univention.admin.syntax
from univention.admin.layout import Group, Tab


if TYPE_CHECKING:
    from collections.abc import Sequence

try:
    from univention.admin.syntax import CMPAttribute, CMPModifier, CMPNegate, CMPOperator, CMPType, CMPValue
except ImportError:
    CMPType, CMPAttribute, CMPNegate, CMPOperator, CMPModifier, CMPValue = univention.admin.syntax.string

log = getLogger('ADMIN')

translation = univention.admin.localization.translation('univention.admin.handlers.authorization')
_ = translation.translate

module = 'authorization/comparison'
operations = ['add', 'edit', 'remove', 'search']
childs = False
default_containers = ['cn=authz,cn=univention']
short_description = _('Authorization: Comparison condition')
object_name = _('Comparison condition')
object_name_plural = _('Comparison condition')
long_description = ''


# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionAuthorizationComparison'],
    ),
}

property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description=_('A unique identifier for this comparison rule.'),
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
    ),
    'description': univention.admin.property(
        short_description=_('Description'),
        long_description=_('A human-readable description of what this comparison is intended to check.'),
        syntax=univention.admin.syntax.string,
        size='Two',
    ),
    'type': univention.admin.property(
        short_description=_('Target type'),
        long_description=_('Select the type of data to compare (e.g., property, DN, UUID).'),
        syntax=CMPType,
        required=True,
    ),
    'attribute': univention.admin.property(
        short_description=_('Target attribute'),
        long_description=_('Specify the name of the attribute or entity to compare. For example, if the type is "Property", use an attribute like "username".'),
        syntax=CMPAttribute,
        required=True,
    ),
    'negation': univention.admin.property(
        short_description=_('Negation'),
        long_description=_('Enable this option to invert the comparison result (i.e., "not equal" instead of "equal")'),
        syntax=CMPNegate,
        required=True,
    ),
    'operator': univention.admin.property(
        short_description=_('Operator'),
        long_description=_('Choose the comparison operator (e.g., equals, greater than, contains).'),
        syntax=CMPOperator,
        required=True,
    ),
    'modifier': univention.admin.property(
        short_description=_('Operator modifier'),
        long_description=_('Optional: Choose a modifier to alter how the operator behaves (e.g., case-insensitive, regex).'),
        syntax=CMPModifier,
        required=False,
    ),
    'value': univention.admin.property(
        short_description=_('Expected value'),
        long_description=_('Enter the value that the selected attribute should be compared to.'),
        syntax=CMPValue,
        required=True,
    ),
}

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('Comparision definition'), layout=[
            ["name"],
            ["description"],
        ]),
        Group(_('Conditions'), layout=[
            ['type', 'attribute'],
            ['negation', 'operator', 'modifier'],
            ['value'],
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
mapping.register('type', 'univentionAuthorizationComparisonType', None, univention.admin.mapping.ListToString)
mapping.register('attribute', 'univentionAuthorizationComparisonAttribute', None, univention.admin.mapping.ListToString)
mapping.register('negation', 'univentionAuthorizationComparisonNegation', None, univention.admin.mapping.ListToString)
mapping.register('operator', 'univentionAuthorizationComparisonOperator', None, univention.admin.mapping.ListToString)
mapping.register('modifier', 'univentionAuthorizationComparisonOperatorModifier', None, univention.admin.mapping.ListToString)
mapping.register('value', 'univentionAuthorizationComparisonValue', None, univention.admin.mapping.ListToString)
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
