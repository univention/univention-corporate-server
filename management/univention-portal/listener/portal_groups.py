#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2019-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import subprocess

from univention.listener import ListenerModuleConfiguration, ListenerModuleHandler


GROUP_CACHE = '/var/cache/univention-portal/groups.json'


class PortalGroups(ListenerModuleHandler):
    def post_run(self):
        with self.as_root():
            subprocess.call(['/usr/sbin/univention-portal', 'update', '--reason', 'ldap:group'])

    class Configuration(ListenerModuleConfiguration):
        description = 'Maintain groups cache for Univention Portal'
        ldap_filter = '(univentionObjectType=groups/group)'
