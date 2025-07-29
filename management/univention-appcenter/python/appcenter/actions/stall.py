#!/usr/bin/python3
#
# Univention App Center
#  univention-app base module for freezing an app
#
# SPDX-FileCopyrightText: 2015-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

from univention.appcenter.actions import StoreAppAction, UniventionAppAction
from univention.appcenter.ucr import ucr_save


class Stall(UniventionAppAction):
    """
    Disables updates for this app. Useful for suppressing
    warnings when an app reached its end of life but shall still
    be used.
    """

    help = 'Stalls an app'

    def setup_parser(self, parser):
        parser.add_argument('app', action=StoreAppAction, help='The ID of the App that shall be stalled')
        parser.add_argument('--undo', action='store_true', help='Reenable a previously stalled app')

    def main(self, args):
        if not args.app.is_installed():
            self.fatal('%s is not installed!' % args.app.id)
            return
        if args.undo:
            self._undo_stall(args.app)
        else:
            self._stall(args.app)

    def _undo_stall(self, app):
        ucr_save({app.ucr_status_key: 'installed', app.ucr_component_key: 'enabled'})

    def _stall(self, app):
        ucr_save({app.ucr_status_key: 'stalled', app.ucr_component_key: 'disabled'})
