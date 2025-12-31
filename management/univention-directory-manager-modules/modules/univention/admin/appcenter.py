#
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from ldap.filter import filter_format

from univention.admin import configRegistry, uexceptions


class AppHost:
    def _get_fqdn(self) -> str | None:
        name = self.info.get('name')
        domainname = self.info.get('domain') or configRegistry.get('domainname')

        if not domainname or not name:
            return None

        return f'{name}.{domainname}'

    def _remove_server_from_app_installed_on_server_list(self):
        fqdn = self._get_fqdn()
        if not fqdn:
            self.log.warning('Could not find FQDN. Skipping removal of computer from apps.')
            return

        apps_installed_on_server = self.lo.search(
            filter=filter_format('(&(objectClass=univentionApp)(univentionAppInstalledOnServer=%s))', [fqdn]),
            base=self.position.getDomain(),
            attr=['univentionAppInstalledOnServer'],
        )

        self.log.debug('found %d apps installed on server %s', len(apps_installed_on_server), fqdn)

        for dn, attrs in apps_installed_on_server:
            self.log.debug('cleaning up app', app=dn)
            newattrs = [attr for attr in attrs['univentionAppInstalledOnServer'] if attr.decode('UTF-8').lower() != fqdn.lower()]

            try:
                self.lo.authz_connection.modify(dn, [('univentionAppInstalledOnServer', attrs['univentionAppInstalledOnServer'], newattrs)])
            except uexceptions.base as err:
                self.log.error('failed to cleanup app... Skipping', app=dn, error=err)
                continue

    def app_host_ldap_post_remove(self):
        self._remove_server_from_app_installed_on_server_list()
