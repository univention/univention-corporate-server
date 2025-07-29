#!/usr/bin/python3
#
# Univention App Center
#  univention-app module for running commands in an app env
#
# SPDX-FileCopyrightText: 2015-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

from univention.appcenter.actions import StoreAppAction
from univention.appcenter.actions.docker_upgrade import Upgrade


class Reinitialize(Upgrade):
    """
    Reinitilizes a Docker App. Essentially removes the container and
    re-creates it with the current settings. Useful for starting the
    container with changed environment variables.
    """

    help = 'Reinitilize Docker App. Mainly used internally.'

    def setup_parser(self, parser):
        parser.add_argument('app', action=StoreAppAction, help='The ID of the App in whose environment COMMANDS shall be executed')

    def main(self, args):
        app = args.app
        if not app.docker:
            self.warn('Only works for Docker Apps')
            return
        if not app.is_installed():
            self.warn('Only works for installed Apps')
            return
        self.old_app = app
        if app.docker_script_setup:
            self.warn('Cannot reinitialize an App with a setup script: Credentials are not passed')
            return
        _args = self._build_namespace(
            call_join_scripts=False,
            configure=False,
            update_certificates=True,
            send_info=False,
            dry_run=False,
            only_master_packages=False,
            skip_checks=[],
            install_master_packages_remotely=False,
            revert=False,
            username=None,
            pwdfile=None,
            password=None,
            set_vars={},
            register_attributes=False,
            register_host=False,
            pull_image=False,
            remove_image=False,
            backup=True,
            noninteractive=True)
        self._upgrade_image(app, _args)
