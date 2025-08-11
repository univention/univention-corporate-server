#!/usr/bin/python3
# SPDX-FileCopyrightText: 2017-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


from univention.listener import ListenerModuleHandler


class ListenerModuleTemplate(ListenerModuleHandler):

    class Configuration:
        name = 'unique_name'
        description = 'listener module description'
        ldap_filter = '(&(objectClass=inetOrgPerson)(uid=example))'
        attributes = ['sn', 'givenName']

    def create(self, dn: str, new: dict[str, list[bytes]]) -> None:
        self.logger.debug('dn: %r', dn)

    def modify(
            self,
            dn: str,
            old: dict[str, list[bytes]],
            new: dict[str, list[bytes]],
            old_dn: str | None,
    ) -> None:
        self.logger.debug('dn: %r', dn)
        if old_dn:
            self.logger.debug('it is (also) a move! old_dn: %r', old_dn)
        self.logger.debug('changed attributes: %r', self.diff(old, new))

    def remove(self, dn: str, old: dict[str, list[bytes]]) -> None:
        self.logger.debug('dn: %r', dn)
