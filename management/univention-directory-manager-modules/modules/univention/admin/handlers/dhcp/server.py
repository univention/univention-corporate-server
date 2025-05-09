#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for |DHCP| servers"""

from typing import Any  # noqa: F401

from ldap.filter import filter_format

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
from univention.admin.layout import Group, Tab

from .__common import DHCPBase


translation = univention.admin.localization.translation('univention.admin.handlers.dhcp')
_ = translation.translate

module = 'dhcp/server'
operations = ['add', 'edit', 'remove', 'search']
superordinate = 'dhcp/service'
childs = False
short_description = _('DHCP: Server')
object_name = _('DHCP server')
object_name_plural = _('DHCP servers')
long_description = _('Associate a service with a server.')
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'dhcpServer'],
    ),

}

property_descriptions = {
    'server': univention.admin.property(
        short_description=_('Server name'),
        long_description=_('The name of the server, which should handle this DHCP service.'),
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        identifies=True,
    ),
}

layout = [
    Tab(_('General'), _('General settings'), layout=[
        Group(_('DHCP server description'), layout=[
            'server',
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('server', 'cn', None, univention.admin.mapping.ListToString)


class object(DHCPBase):
    module = module

    def _ldap_addlist(self):
        # type: () -> list[tuple[str, Any]]
        searchBase = self.position.getDomain()
        if self.lo.authz_connection.searchDn(base=searchBase, filter=filter_format('(&(objectClass=dhcpServer)(cn=%s))', [self.info['server']])):
            raise univention.admin.uexceptions.dhcpServerAlreadyUsed(self.info['server'])

        al = super()._ldap_addlist()
        return [*al, ('dhcpServiceDN', self.superordinate.dn.encode('UTF-8'))]

    def _ldap_post_move(self, olddn):
        # type: (str) -> None
        """edit dhcpServiceDN"""
        super()._ldap_post_move(olddn)
        oldServiceDN = self.lo.authz_connection.getAttr(self.dn, 'dhcpServiceDN')
        module = univention.admin.modules.identifyOne(self.position.getDn(), self.lo.authz_connection.get(self.position.getDn()))
        obj = univention.admin.objects.get(module, None, self.lo, self.position, dn=self.position.getDn())
        _shadow_module, shadow_object = univention.admin.objects.shadow(self.lo, module, obj, self.position)
        self.lo.authz_connection.modify(self.dn, [('dhcpServiceDN', oldServiceDN[0], shadow_object.dn.encode('UTF-8'))])

    @classmethod
    def lookup_filter_superordinate(cls, filter, superordinate):
        # type: (univention.admin.filter.conjunction, univention.admin.handlers.simpleLdap) -> univention.admin.filter.conjunction
        filter.expressions.append(univention.admin.filter.expression('dhcpServiceDN', superordinate.dn, escape=True))
        return filter


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
