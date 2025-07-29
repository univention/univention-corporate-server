#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for all mail objects"""

from __future__ import annotations

import univention.admin
import univention.admin.filter
import univention.admin.handlers
import univention.admin.handlers.mail.domain
import univention.admin.handlers.mail.folder
import univention.admin.handlers.mail.lists
import univention.admin.localization
import univention.admin.uldap
from univention.admin.layout import Tab


translation = univention.admin.localization.translation('univention.admin.handlers.mail')
_ = translation.translate


module = 'mail/mail'

childs = False
short_description = _('Mail')
object_name = _('Mail object')
object_name_plural = _('Mail objects')
long_description = ''
operations = ['search']
childmodules = ["mail/folder", "mail/domain", "mail/lists"]
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
layout = [Tab(_('General'), _('Basic settings'), ["name"])]

mapping = univention.admin.mapping.mapping()


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
