#!/usr/bin/python3
#
# Univention App Center
#  univention-app module for uninstalling an app
#
# SPDX-FileCopyrightText: 2015-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import os.path

from univention.admindiary.client import write_event
from univention.admindiary.events import APP_REMOVE_FAILURE, APP_REMOVE_START, APP_REMOVE_SUCCESS
from univention.appcenter.actions.install_base import InstallRemoveUpgrade
from univention.appcenter.exceptions import RemoveFailed
from univention.appcenter.packages import remove_packages, remove_packages_dry_run, update_packages
from univention.appcenter.ucr import ucr_save


class Remove(InstallRemoveUpgrade):
    """Removes an application from the Univention App Center."""

    help = 'Uninstall an app'

    prescript_ext = 'prerm'
    pre_readme = 'readme_uninstall'
    post_readme = 'readme_post_uninstall'

    def main(self, args):
        return self.do_it(args)

    def _show_license(self, app, args):
        pass

    def _do_it(self, app, args):
        self._unregister_listener(app)
        self.percentage = 5
        if not self._remove_app(app, args):
            raise RemoveFailed()
        self.percentage = 45
        self._unregister_app(app, args)
        self.percentage = 55
        self._unregister_attributes(app, args)
        self.percentage = 60
        if self._unregister_component(app):
            update_packages()
        self.percentage = 70
        self._unregister_files(app)
        self.percentage = 80
        self._call_unjoin_script(app, args)
        if not app.docker:
            ucr_save({'appcenter/prudence/docker/%s' % app.id: 'yes'})

    def _write_start_event(self, app, args):
        return write_event(APP_REMOVE_START, {'name': app.name, 'version': app.version}, username=self._get_username(args))

    def _write_success_event(self, app, context_id, args):
        return write_event(APP_REMOVE_SUCCESS, {'name': app.name, 'version': app.version}, username=self._get_username(args), context_id=context_id)

    def _write_fail_event(self, app, context_id, status, args):
        return write_event(APP_REMOVE_FAILURE, {'name': app.name, 'version': app.version, 'error_code': str(status)}, username=self._get_username(args), context_id=context_id)

    def _call_action_hooks(self, directory):
        super()._run_parts(directory)

    def needs_credentials(self, app):
        return bool(os.path.exists(app.get_cache_file(self.prescript_ext)))

    def _remove_app(self, app, args):
        self._configure(app, args)
        return remove_packages(app.get_packages(additional=False))

    def _dry_run(self, app, args):
        return remove_packages_dry_run(app.get_packages(additional=False))
