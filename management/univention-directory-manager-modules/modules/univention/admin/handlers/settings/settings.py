# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for all setting objects"""

from __future__ import annotations

import univention.admin
import univention.admin.handlers
import univention.admin.handlers.settings.default
import univention.admin.handlers.settings.directory
import univention.admin.handlers.settings.license
import univention.admin.handlers.settings.usertemplate
import univention.admin.localization
import univention.admin.uldap


translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/settings'
superordinate = 'settings/cn'
childs = False
short_description = _('Preferences')
object_name = _('Preference')
object_name_plural = _('Preferences')
long_description = ''
operations = ['search']
virtual = True
options: dict[str, univention.admin.option] = {}
property_descriptions: dict[str, univention.admin.property] = {}

mapping = univention.admin.mapping.mapping()


class object(univention.admin.handlers.simpleLdap):
    module = module


def lookup(
    co: None,
    lo: univention.admin.uldap.access,
    filter_s: str,
    base: str = '',
    superordinate: univention.admin.handlers.simpleLdap | None = None,
    scope: str = 'sub',
    unique: bool = False,
    required: bool = False,
    timeout: int = -1,
    sizelimit: int = 0,
) -> list[univention.admin.handlers.simpleLdap]:
    return [
        obj
        for mod in (
            univention.admin.handlers.settings.directory,
            univention.admin.handlers.settings.default,
            univention.admin.handlers.settings.usertemplate,
            univention.admin.handlers.settings.license,
        )
        for obj in mod.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
    ]


def identify(dn: str, attr: univention.admin.handlers._Attributes, canonical: bool = False) -> None:
    pass
