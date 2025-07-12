# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for all computer objects"""

from __future__ import annotations

import univention.admin
import univention.admin.handlers
import univention.admin.handlers.computers
import univention.admin.localization
import univention.admin.mapping
import univention.admin.syntax
import univention.admin.uldap


translation = univention.admin.localization.translation('univention.admin.handlers.computers')
_ = translation.translate

module = 'computers/computer'
childmodules = [computer.module for computer in univention.admin.handlers.computers.computers]
childs = False
short_description = _('Computer')
object_name = _('Computer')
object_name_plural = _('Computers')
long_description = ''
operations = ['search']
virtual = True
options: dict[str, univention.admin.option] = {}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description='',
        syntax=univention.admin.syntax.hostName,
        include_in_default_search=True,
        required=True,
        identifies=True,
        ldap_attribute='cn',
    ),
    'dnsAlias': univention.admin.property(
        short_description=_('DNS alias'),
        long_description='',
        syntax=univention.admin.syntax.string,
        multivalue=True,
    ),
    'description': univention.admin.property(
        short_description=_('Description'),
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        ldap_attribute='description',
    ),
    'mac': univention.admin.property(
        short_description=_('MAC address'),
        long_description='',
        syntax=univention.admin.syntax.string,
        multivalue=True,
        include_in_default_search=True,
        ldap_attribute='macAddress',
        encoding='ASCII',
    ),
    'ip': univention.admin.property(
        short_description=_('IP address'),
        long_description='',
        syntax=univention.admin.syntax.ipAddress,
        multivalue=True,
        include_in_default_search=True,
    ),
    'inventoryNumber': univention.admin.property(
        short_description=_('Inventory number'),
        long_description='',
        syntax=univention.admin.syntax.string,
        multivalue=True,
        include_in_default_search=True,
        ldap_attribute='univentionInventoryNumber',
    ),
    'fqdn': univention.admin.property(
        short_description='FQDN',
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        may_change=False,
        dontsearch=True,
    ),
}

mapping = univention.admin.mapping.mapping()
mapping.from_properties(property_descriptions)


class object(univention.admin.handlers.simpleLdap):
    module = module

    def open(self) -> None:
        super().open()
        if 'name' in self.info and 'domain' in self.info:
            # in syntax.py IComputer_FQDN key and label are '%(name)s.%(domain)s' for
            #   performance reasons. These statements and this fqdn over here have to
            #   be in sync.
            self['fqdn'] = '%s.%s' % (self['name'], self['domain'])
            self.save()


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
    for computer in univention.admin.handlers.computers.computers:
        res += computer.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
    return res


def identify(dn: str, attr: univention.admin.handlers._Attributes, canonical: bool = False) -> None:
    pass
