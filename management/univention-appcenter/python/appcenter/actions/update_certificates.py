#!/usr/bin/python3
#
# Univention App Center
#  univention-app module for configuring an app
#
# SPDX-FileCopyrightText: 2015-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

from tempfile import NamedTemporaryFile

from univention.appcenter.actions import StoreAppAction, UniventionAppAction
from univention.appcenter.app_cache import Apps
from univention.appcenter.log import get_logfile_logger
from univention.appcenter.utils import get_locale


class UpdateCertificates(UniventionAppAction):
    """Update certificates for an application."""

    help = 'Update certificates for an app'

    def setup_parser(self, parser):
        super().setup_parser(parser)
        parser.add_argument('apps', nargs='*', action=StoreAppAction, help='The ID of app for which the certificates should be updated (all locally installed if none given)')

    def update_certificates(self, app):
        self._run_update_certificates_script(app)

    def main(self, args):
        if not args.apps:
            args.apps = Apps().get_all_locally_installed_apps()
        self.logfile_logger = get_logfile_logger('update-certificates')
        for app in args.apps:
            self.log(f'updating certificates for {app}')
            self.update_certificates(app)

    def _run_update_certificates_script(self, app):
        ext = 'update_certificates'
        with NamedTemporaryFile('r') as error_file:
            kwargs = {}
            kwargs['version'] = app.version
            kwargs['error_file'] = error_file.name
            locale = get_locale()
            if locale:
                kwargs['locale'] = locale
            success = self._call_cache_script(app, ext, **kwargs)
            if success is False:
                for line in error_file:
                    self.fatal(line)
            return success
