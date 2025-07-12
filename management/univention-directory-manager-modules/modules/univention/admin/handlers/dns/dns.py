# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for all |DNS| objects"""

from __future__ import annotations

import univention.admin
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.uldap
from univention.admin.layout import Tab


translation = univention.admin.localization.translation('univention.admin.handlers.dns')
_ = translation.translate


module = 'dns/dns'

childs = False
short_description = _('All DNS zones')
object_name = _('DNS zone')
object_name_plural = _('DNS zones')
long_description = _('Manage the Domain Name System.')
operations = ['search']
childmodules = ['dns/forward_zone', 'dns/reverse_zone']
virtual = True
options: dict[str, univention.admin.option] = {}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description='',
        syntax=univention.admin.syntax.dnsName,
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


def rewrite(filter_s: str, **args: str) -> str:
    if not filter_s:
        return filter_s
    filter_p = univention.admin.filter.parse(filter_s)
    mapping = univention.admin.mapping.mapping()
    for key, value in args.items():
        mapping.register(key, value)
    univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
    return str(filter_p)


MAP_SEARCH = {
    'dns/forward_zone': 'zone',
    'dns/reverse_zone': 'subnet',
    'dns/ptr_record.py': 'address',
}


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
        try:
            attr = MAP_SEARCH[childmodule]
        except LookupError:
            fltr = filter_s
        else:
            fltr = rewrite(filter_s, name=attr)
        res += mod.lookup(co, lo, fltr, base, superordinate, scope, unique, required, timeout, sizelimit)
    return res


def identify(dn: str, attr: univention.admin.handlers._Attributes, canonical: bool = False) -> None:
    pass
