#!/usr/bin/python3
#
# Univention Management Console
#  module: software management
#
# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import json

from univention.appcenter.actions import UniventionAppAction, get_action


class UmcGenerateAppCache(UniventionAppAction):

    help = 'Generates the app cache /var/cache/univention-appcenter/umc-query.json'
    CACHE_FILE = '/var/cache/univention-appcenter/umc-query.json'

    def main(self, args=None):
        self.generate()

    @classmethod
    def generate(cls):
        list_apps = get_action('list')
        domain = get_action('domain')
        apps = list_apps.get_apps()
        info = domain.to_dict(apps)
        with open(cls.CACHE_FILE, 'w') as fd:
            json.dump(info, fd)
        return info

    @classmethod
    def load(cls):
        try:
            with open(cls.CACHE_FILE) as fd:
                return json.load(fd)
        except (OSError, ValueError) as exc:
            cls.warn('Error returning cached query: %s' % exc)
            return []
