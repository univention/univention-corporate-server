# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for printer shares"""

from __future__ import annotations

import univention.admin
import univention.admin.handlers
import univention.admin.localization
import univention.admin.uldap


translation = univention.admin.localization.translation('univention.admin.handlers.shares')
_ = translation.translate

module = 'shares/print'
childmodules = ['shares/printer', 'shares/printergroup']
childs = False
short_description = _('Printer share')
object_name = _('Printer share')
object_name_plural = _('Printer shares')
long_description = ''
operations = ['search']
virtual = True
options: dict[str, univention.admin.option] = {}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description='',
        syntax=univention.admin.syntax.printerName,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
    ),
    'spoolHost': univention.admin.property(
        short_description=_('Print server'),
        long_description='',
        syntax=univention.admin.syntax.ServicePrint_FQDN,
        multivalue=True,
        required=True,
    ),
    'sambaName': univention.admin.property(
        short_description=_('Windows name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        unique=True,
    ),
}

mapping = univention.admin.mapping.mapping()


class object(univention.admin.handlers.simpleLdap):
    module = module
    default_containers_attribute_name = 'printers'


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
    res: list[univention.admin.handlers.simpleLdap] = []
    for child in childmodules:
        mod = univention.admin.modules._get(child)
        res += mod.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
    return res


def identify(dn: str, attr: univention.admin.handlers._Attributes, canonical: bool = False) -> None:
    pass
