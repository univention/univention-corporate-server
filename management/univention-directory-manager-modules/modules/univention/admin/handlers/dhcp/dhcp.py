# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| for all |DHCP| objects"""

from __future__ import annotations

import univention.admin
import univention.admin.handlers
import univention.admin.localization
import univention.admin.uldap
from univention.admin.layout import Tab


translation = univention.admin.localization.translation('univention.admin.handlers.dhcp')
_ = translation.translate


module = 'dhcp/dhcp'

childs = False
childmodules = ['dhcp/service']
short_description = _('All DHCP services')
object_name = _('DHCP service')
object_name_plural = _('DHCP services')
long_description = _('Manage the Domain Host Configuration Protocol service.')
operations = ['search']
virtual = True
options: dict[str, univention.admin.option] = {}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        identifies=True,
    ),
}

layout = [Tab(_('General'), _('Basic settings'), layout=['name'])]

mapping = univention.admin.mapping.mapping()
mapping.from_properties(property_descriptions)


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
    sup = univention.admin.modules._get(superordinate.module) if superordinate else None
    res: list[univention.admin.handlers.simpleLdap] = []
    for childmodule in sup.childmodules if sup else childmodules:
        mod = univention.admin.modules._get(childmodule)
        res += mod.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
    return res


def identify(dn: str, attr: univention.admin.handlers._Attributes, canonical: bool = False) -> None:
    pass
