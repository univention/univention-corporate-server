#!/usr/bin/python3
#
# Univention App Center
#  univention-app module for searching for available upgrading
#
# SPDX-FileCopyrightText: 2015-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

from univention.appcenter.actions import StoreAppAction, UniventionAppAction
from univention.appcenter.app_cache import Apps
from univention.appcenter.ucr import ucr_is_true, ucr_save


class UpgradeSearch(UniventionAppAction):
    """Searches for available upgrades of apps."""

    help = 'Searches for upgrades'

    def setup_parser(self, parser):
        parser.add_argument('app', nargs='*', action=StoreAppAction, help='The ID of the App')
        parser.add_argument('--do-not-update', action='store_false', dest='update', help='Do not download new ini files from the App Center server')

    def main(self, args):
        from univention.appcenter.actions import get_action
        if args.update:
            get_action('update').call()
        apps = args.app
        if not apps:
            apps = Apps().get_all_locally_installed_apps()
        for app in apps:
            self.debug('Checking %s' % app)
            if not app.is_installed():
                continue
            upgrade_available = self._check_for_upgrades(app)
            if upgrade_available is True:
                ucr_save({app.ucr_upgrade_key: 'yes'})
            elif upgrade_available is False:
                ucr_save({app.ucr_upgrade_key: None})
        return any(ucr_is_true(app.ucr_upgrade_key) for app in apps)

    def _check_for_upgrades(self, app):
        return Apps().find_candidate(app) is not None
