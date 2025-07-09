#
# SPDX-FileCopyrightText: 2024-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for all |blocklist| objects"""

from __future__ import annotations

import univention.admin
import univention.admin.blocklist
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.uldap
from univention.admin.layout import Tab


translation = univention.admin.localization.translation('univention.admin.handlers.blocklists')
_ = translation.translate


module = 'blocklists/all'

childs = False
short_description = _('All blocklist objects')
object_name = _('Blocklist')
object_name_plural = _('Blocklists')
long_description = _('Manage the blocklists')
operations = ['search']
childmodules = ['blocklists/list']
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


class object(univention.admin.handlers.simpleLdap):
    module = module
    ldap_base = univention.admin.blocklist.BLOCKLIST_BASE


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
    if not superordinate:
        filter_s = ''
        base = univention.admin.blocklist.BLOCKLIST_BASE
    sup = univention.admin.modules._get(superordinate.module) if superordinate else None
    res: list[univention.admin.handlers.simpleLdap] = []
    for childmodule in sup.childmodules if sup else childmodules:
        mod = univention.admin.modules._get(childmodule)
        res += mod.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
    return res


def identify(dn: str, attr: univention.admin.handlers._Attributes, canonical: bool = False) -> None:
    pass
