# SPDX-FileCopyrightText: 2015-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| policy utilities"""

from __future__ import annotations

from typing import Any

import univention.admin.localization
import univention.admin.syntax
from univention.admin.layout import Tab
from univention.admin.mapping import ListToString, mapping as MappingType


translation = univention.admin.localization.translation('univention.admin')
_ = translation.translate


def register_policy_mapping(mapping: MappingType) -> None:
    mapping.register('requiredObjectClasses', 'requiredObjectClasses')
    mapping.register('prohibitedObjectClasses', 'prohibitedObjectClasses')
    mapping.register('fixedAttributes', 'fixedAttributes')
    mapping.register('emptyAttributes', 'emptyAttributes')
    mapping.register('ldapFilter', 'ldapFilter', None, ListToString)


def policy_object_tab() -> Tab:
    return Tab(_('Object'), _('Object'), advanced=True, layout=[
        ['ldapFilter'],
        ['requiredObjectClasses', 'prohibitedObjectClasses'],
        ['fixedAttributes', 'emptyAttributes'],
    ])


def requiredObjectClassesProperty(**kwargs: Any) -> tuple[str, univention.admin.property]:
    pargs = {
        "short_description": _('Required object class'),
        "long_description": '',
        "syntax": univention.admin.syntax.ldapObjectClass,
        "multivalue": True,
    }
    pargs.update(kwargs)
    return 'requiredObjectClasses', univention.admin.property(**pargs)


def prohibitedObjectClassesProperty(**kwargs: Any) -> tuple[str, univention.admin.property]:
    pargs = {
        "short_description": _('Excluded object class'),
        "long_description": '',
        "syntax": univention.admin.syntax.ldapObjectClass,
        "multivalue": True,
    }
    pargs.update(kwargs)
    return 'prohibitedObjectClasses', univention.admin.property(**pargs)


def fixedAttributesProperty(**kwargs: Any) -> tuple[str, univention.admin.property]:
    pargs = {
        "short_description": _('Fixed attribute'),
        "long_description": '',
        "multivalue": True,
    }
    pargs.update(kwargs)
    return 'fixedAttributes', univention.admin.property(**pargs)


def emptyAttributesProperty(**kwargs: Any) -> tuple[str, univention.admin.property]:
    pargs = {
        "short_description": _('Empty attribute'),
        "long_description": '',
        "multivalue": True,
    }
    pargs.update(kwargs)
    return 'emptyAttributes', univention.admin.property(**pargs)


def ldapFilterProperty(**kwargs: Any) -> tuple[str, univention.admin.property]:
    pargs = {
        "short_description": _('LDAP filter'),
        "long_description": _('This policy applies only to objects which matches this LDAP filter.'),
        "syntax": univention.admin.syntax.ldapFilter,
    }
    pargs.update(kwargs)
    return 'ldapFilter', univention.admin.property(**pargs)
