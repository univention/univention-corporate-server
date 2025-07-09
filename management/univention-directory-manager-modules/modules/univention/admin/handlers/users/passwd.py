# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for password part of the user"""

from __future__ import annotations

import univention.admin
import univention.admin.filter
import univention.admin.handlers
import univention.admin.handlers.users.user
import univention.admin.localization
import univention.admin.uexceptions
import univention.admin.uldap
from univention.admin.layout import Tab


translation = univention.admin.localization.translation('univention.admin.handlers.users')
_ = translation.translate

module = 'users/passwd'
operations = ['edit']

childs = False
short_description = _('User: Password')
object_name = _('Password')
object_name_plural = _('Passwords')
long_description = ''
options: dict[str, univention.admin.option] = {}
# fmt: off
property_descriptions = {
    'username': univention.admin.property(
        short_description=_('User name'),
        long_description='',
        syntax=univention.admin.syntax.uid,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
    ),
    'password': univention.admin.property(
        short_description=_('Password'),
        long_description='',
        syntax=univention.admin.syntax.userPasswd,
        required=True,
        dontsearch=True,
    ),
}

layout = [
    Tab(_('Change password'), _('Change password'), [
        'password']),
]
# fmt: on

object = univention.admin.handlers.users.user.object


def lookup(co: None, lo: univention.admin.uldap.access, filter_s: str, base: str = '', superordinate: univention.admin.handlers.simpleLdap | None = None, scope: str = 'sub', unique: bool = False, required: bool = False, timeout: int = -1, sizelimit: int = 0) -> list[univention.admin.handlers.simpleLdap]:
    dn = lo.whoami()
    return [user for user in univention.admin.handlers.users.user.lookup(co, lo, filter_s, base, superordinate, scope=scope, unique=unique, required=required, timeout=timeout, sizelimit=sizelimit) if lo.compare_dn(dn, user.dn)]
