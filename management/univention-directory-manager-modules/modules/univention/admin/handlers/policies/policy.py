#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for all policies"""

from __future__ import annotations

import univention.admin.filter
import univention.admin.handlers
import univention.admin.handlers.policies
import univention.admin.localization
from univention.admin.layout import Tab


translation = univention.admin.localization.translation('univention.admin.handlers.policies')
_ = translation.translate


module = 'policies/policy'

childs = False
short_description = _('Policy')
object_name = _('Policy')
object_name_plural = _('Policies')
long_description = ''
help_link = _('https://docs.software-univention.de/manual-5.2.html#central:policies')
help_text = _(
    '<p>Policies are objects that can be connected with other objects in the directory tree. Connected policies allow to define object properties in a unified manner. Policies that are connected with containers or organizational units are inherited by all objects located below.</p><p>More information can be found in the <a href="https://docs.software-univention.de/manual-5.2.html#central:policies" target="_blank">online documentation for UCS</a>.</p>',
)
operations = ['search']
childmodules = []
for pol in univention.admin.handlers.policies.policies:
    if hasattr(pol, 'module'):
        childmodules.append(pol.module)
virtual = True
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description='',
        syntax=univention.admin.syntax.policyName,
        include_in_default_search=True,
        required=True,
        identifies=True,
    ),
}
layout = [Tab(_('General'), _('Basic settings'), layout=['name'])]

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
    res: list[univention.admin.handlers.simpleLdap] = []
    for pol in univention.admin.handlers.policies.policies:
        res += pol.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
    return res


def identify(dn: str, attr: univention.admin.handlers._Attributes, canonical: bool = False) -> None:
    pass
