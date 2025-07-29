#!/usr/bin/python3
#
# Univention RADIUS
#  Listener integration
#
# SPDX-FileCopyrightText: 2019-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import subprocess

from univention.listener.handler import ListenerModuleHandler


class AppListener(ListenerModuleHandler):
    run_update = False

    class Configuration(ListenerModuleHandler.Configuration):
        description = 'Listener module for univention-radius'
        ldap_filter = '(objectClass=univentionHost)'

    def create(self, dn: str, new: dict[str, list[bytes]]) -> None:
        if b'univentionRadiusClient' in new.get('objectClass', []):
            self.run_update = True
            self.logger.info('config update triggered')

    def modify(self, dn: str, old: dict[str, list[bytes]], new: dict[str, list[bytes]], old_dn: str | None) -> None:
        # only update the file, if relevant
        if old_dn:
            self.run_update = True
            self.logger.info('config update triggered (move)')
        elif (b'univentionRadiusClient' in old.get('objectClass', []) or b'univentionRadiusClient' in new.get('objectClass', [])) and (  # noqa: PLR0916
            set(old.get('univentionRadiusClientSharedSecret', [])) != set(new.get('univentionRadiusClientSharedSecret', []))
            or set(old.get('univentionRadiusClientType', [])) != set(new.get('univentionRadiusClientType', []))
            or set(old.get('univentionRadiusClientVirtualServer', [])) != set(new.get('univentionRadiusClientVirtualServer', []))
            or set(old.get('aRecord', [])) != set(new.get('aRecord', []))
            or set(old.get('aAAARecord', [])) != set(new.get('aAAARecord', []))
        ):
            self.run_update = True
            self.logger.info('config update triggered')

    def remove(self, dn: str, old: dict[str, list[bytes]]) -> None:
        if b'univentionRadiusClient' in old.get('objectClass', []):
            self.run_update = True
            self.logger.info('config update triggered')

    def post_run(self) -> None:
        if self.run_update:
            self.run_update = False
            with self.as_root():
                self.logger.info('Updating clients.univention.conf')
                subprocess.call(['/usr/sbin/univention-radius-update-clients-conf'])
                self.logger.info('Restarting freeradius')
                subprocess.call(['systemctl', 'try-restart', 'freeradius'])
