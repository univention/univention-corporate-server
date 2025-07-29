#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for all nagios settings"""

from __future__ import annotations

import univention.admin
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.uldap


translation = univention.admin.localization.translation('univention.admin.handlers.nagios')
_ = translation.translate

module = 'nagios/nagios'
help_link = _('https://docs.software-univention.de/manual/5.0/en/monitoring/nagios.html#nagios-general')
default_containers = ['cn=nagios']

childmodules = ['nagios/service']

childs = False
short_description = _('Nagios object')
object_name = _('Nagios object')
object_name_plural = _('Nagios objects')
long_description = ''
operations = ['search']
virtual = True
options: dict[str, univention.admin.option] = {}

property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description=_('Nagios object name'),
        syntax=univention.admin.syntax.string_numbers_letters_dots,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
    ),
}

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
    module = module


def lookup(co: None, lo: univention.admin.uldap.access, filter_s: str, base: str = '', superordinate: univention.admin.handlers.simpleLdap | None = None, scope: str = 'sub', unique: bool = False, required: bool = False, timeout: int = -1, sizelimit: int = 0) -> list[univention.admin.handlers.simpleLdap]:
    res: list[univention.admin.handlers.simpleLdap] = []
    for childmodule in childmodules:
        mod = univention.admin.modules._get(childmodule)
        res += mod.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
    return res


def identify(dn: str, attr: univention.admin.handlers._Attributes, canonical: bool = False) -> None:
    pass
