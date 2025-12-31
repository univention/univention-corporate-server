# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for printer modules"""

from __future__ import annotations

import shlex

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.syntax
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/printermodel'
operations = ['add', 'edit', 'remove', 'search', 'move']
superordinate = 'settings/cn'

childs = False
short_description = _('Settings: Printer Driver List')
object_name = _('Printer Driver List')
object_name_plural = _('Printer Driver Lists')
long_description = _('List of drivers for printers')
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionPrinterModels'],
    ),
}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description=_('Name'),
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        identifies=True,
    ),
    'printmodel': univention.admin.property(
        short_description=_('Printer Model'),
        long_description=_('Printer Model'),
        syntax=univention.admin.syntax.printerModel,
        multivalue=True,
        include_in_default_search=True,
    ),
}

layout = [
    Tab(_('General'), _('Printer List'), layout=[
        Group(_('General printer driver list settings'), layout=[
            'name',
            'printmodel',
        ]),
    ]),
]
# fmt: on


def unmapDriverList(ldap_value: list[bytes], encoding: univention.admin.handlers._Encoding = ()) -> list[list[str]]:
    return [shlex.split(x.decode(*encoding)) for x in ldap_value]


def mapDriverList(udm_value: list[str], encoding: univention.admin.handlers._Encoding = ()) -> list[bytes]:
    def q(s: str) -> str:
        return s.replace('"', '\\"')

    ldap_attr_list = []
    for x in udm_value:
        value = '"%s" "%s"' % (q(x[0]), q(x[1]))
        ldap_attr_list.append(value.encode(*encoding))
    return ldap_attr_list


# fmt: off
mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('printmodel', 'printerModel', mapDriverList, unmapDriverList)
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module

    @classmethod
    def rewrite_filter(cls, filter: univention.admin.filter.expression, mapping: univention.admin.mapping.mapping) -> None:
        if filter.variable == 'printmodel':
            filter.variable = 'printerModel'
        else:
            super().rewrite_filter(filter, mapping)


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
