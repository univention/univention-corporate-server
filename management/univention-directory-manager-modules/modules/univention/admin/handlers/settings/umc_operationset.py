#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2011-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for |UMC| operation set objects"""

from __future__ import annotations

import univention.admin
import univention.admin.mapping as udm_mapping
import univention.admin.syntax as udm_syntax
from univention.admin.handlers import simpleLdap
from univention.admin.layout import Group, Tab
from univention.admin.localization import translation


_ = translation('univention.admin.handlers.settings').translate

module = 'settings/umc_operationset'
operations = ('add', 'edit', 'remove', 'search', 'move')
superordinate = 'settings/cn'

childs = False
short_description = _('Settings: UMC operation set')
object_name = _('UMC operation set')
object_name_plural = _('UMC operation sets')
long_description = _('List of Operations for UMC')
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'umcOperationSet'],
    ),
}

property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description='',
        syntax=udm_syntax.string,
        include_in_default_search=True,
        required=True,
        identifies=True,
    ),
    'description': univention.admin.property(
        short_description=_('Description'),
        long_description='',
        syntax=udm_syntax.string,
        include_in_default_search=True,
        dontsearch=True,
        required=True,
    ),
    'operation': univention.admin.property(
        short_description=_('UMC commands'),
        long_description=_('List of UMC command names or patterns'),
        syntax=udm_syntax.UMC_CommandPattern,
        multivalue=True,
        dontsearch=True,
    ),
    'flavor': univention.admin.property(
        short_description=_('Flavor'),
        long_description=_('Defines a specific flavor of the UMC module. If given the operations are permitted only if the flavor matches.'),
        syntax=udm_syntax.string,
        include_in_default_search=True,
        dontsearch=True,
    ),
    'hosts': univention.admin.property(
        short_description=_('Restrict to host'),
        long_description=_('Defines on which hosts this operations are permitted on. The value can be either a host name (as filename pattern e.g. server1*), a server role (e.g. serverrole:domaincontroller_slave) or a service, which must run on the host, (e.g. service:LDAP). Leaving this empty causes all hosts to be allowed.'),
        syntax=udm_syntax.string,
        multivalue=True,
        dontsearch=True,
    ),
}

layout = [
    Tab(_('General'), _('UMC Operation Set'), layout=[
        Group(_('General UMC operation set settings'), layout=[
            ['name', 'description'],
            'operation',
            'flavor',
            'hosts',
        ]),
    ]),
]


def mapUMC_CommandPattern(udm_value: list[list[str]], encoding: univention.admin.handlers._Encoding = ()) -> list[bytes]:
    return [':'.join(x).encode(*encoding) for x in udm_value]


def unmapUMC_CommandPattern(ldap_value: list[bytes], encoding: univention.admin.handlers._Encoding = ()) -> list[tuple[str, str]]:
    return [
        val.decode(*encoding).partition(":")[::2]
        for val in ldap_value
    ]


mapping = udm_mapping.mapping()
mapping.register('name', 'cn', None, udm_mapping.ListToString)
mapping.register('description', 'description', None, udm_mapping.ListToString)
mapping.register('operation', 'umcOperationSetCommand', mapUMC_CommandPattern, unmapUMC_CommandPattern)
mapping.register('flavor', 'umcOperationSetFlavor', None, udm_mapping.ListToString)
mapping.register('hosts', 'umcOperationSetHost')


class object(simpleLdap):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
