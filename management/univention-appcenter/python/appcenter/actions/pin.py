#!/usr/bin/python3
#
# Univention App Center
#  univention-app base module for freezing an app
#
# SPDX-FileCopyrightText: 2023-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

from univention.appcenter.actions import StoreAppAction, UniventionAppAction
from univention.appcenter.ucr import ucr_save


class Pin(UniventionAppAction):
    """
    Disables upgrades for this app. Also does not allow
    to remove this app. Useful when a newer app version
    is available, but due to issues with the new version the
    current version should not be upgraded or removed.
    """

    help = 'Pins or unpins an app version'

    def setup_parser(self, parser):
        parser.add_argument('app', action=StoreAppAction, help='The ID of the App that shall be pinned or unpinned')
        parser.add_argument('--revert', action='store_true', help='Unpin previously pinned app')

    def main(self, args):
        if not args.app.is_installed():
            self.fatal('%s is not installed!' % args.app.id)
            return
        if args.revert:
            self._unpin(args.app)
        else:
            self._pin(args.app)

    def _unpin(self, app):
        ucr_save({app.ucr_pinned_key: None})

    def _pin(self, app):
        ucr_save({app.ucr_pinned_key: 'true'})
