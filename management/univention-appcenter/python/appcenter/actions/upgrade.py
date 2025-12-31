#!/usr/bin/python3
#
# Univention App Center
#  univention-app module for upgrading an app
#
# SPDX-FileCopyrightText: 2015-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

from univention.admindiary.client import write_event
from univention.admindiary.events import APP_UPGRADE_FAILURE, APP_UPGRADE_START, APP_UPGRADE_SUCCESS
from univention.appcenter.actions.install import Install
from univention.appcenter.app_cache import Apps
from univention.appcenter.packages import dist_upgrade, install_packages
from univention.appcenter.ucr import ucr_is_true


class Upgrade(Install):
    """Upgrades an installed application from the Univention App Center."""

    help = 'Upgrade an app'

    pre_readme = 'readme_update'
    post_readme = 'readme_post_update'

    def __init__(self):
        super().__init__()
        # original_app: The App installed when the whole action started
        # old_app: The current App installed when trying to upgrade
        #   - should be the same most of the time. But Docker Apps may upgrade
        #   themselves multiple times during one run and old_app will be set
        #   after each iteration
        self.original_app = self.old_app = None

    def setup_parser(self, parser):
        super(Install, self).setup_parser(parser)
        parser.add_argument('--only-master-packages', action='store_true', help='Install only Primary Node packages')
        parser.add_argument('--do-not-install-master-packages-remotely', action='store_false', dest='install_master_packages_remotely', help='Do not install Primary Node packages on Primary or Backup Directory Node systems')

    def _app_too_old(self, current_app, specified_app):
        if current_app >= specified_app:
            self.fatal('A newer version of %s than the one installed must be present and chosen' % current_app.id)
            return True
        return False

    def main(self, args):
        apps = args.app
        real_apps = []
        for app in apps:
            old_app = Apps().find(app.id)
            if app == old_app:
                app = Apps().find_candidate(app) or app
            if not args.only_master_packages:  # always allow only_master_packages
                if self._app_too_old(old_app, app):
                    continue
            real_apps.append(app)
        if not real_apps:
            return
        args.app = real_apps
        return self.do_it(args)

    def do_it_once(self, app, args):
        self.old_app = self.original_app = Apps().find(app.id)
        return super().do_it_once(app, args)

    def _write_start_event(self, app, args):
        return write_event(APP_UPGRADE_START, {'name': app.name, 'version': self.old_app.version}, username=self._get_username(args))

    def _write_success_event(self, app, context_id, args):
        return write_event(APP_UPGRADE_SUCCESS, {'name': app.name, 'version': app.version}, username=self._get_username(args), context_id=context_id)

    def _write_fail_event(self, app, context_id, status, args):
        return write_event(APP_UPGRADE_FAILURE, {'name': app.name, 'version': self.old_app.version, 'error_code': str(status)}, username=self._get_username(args), context_id=context_id)

    def _call_action_hooks(self, directory):
        super()._run_parts(directory)

    def needs_credentials(self, app):
        needs_credentials = super().needs_credentials(app)
        if needs_credentials:
            return True
        if app.docker and app.docker_script_update_packages:
            return True
        return bool(app.docker and app.docker_script_update_app_version)

    def _revert(self, app, args):
        try:
            self.log('Trying to revert to old version. This may lead to problems, but it is better than leaving it the way it is now')
            args.revert = False
            self._do_it(self.old_app, args)
        except Exception:
            pass

    def _show_license(self, app, args):
        old_app = Apps().find(app.id)
        if app.license_agreement != old_app.license_agreement:
            return super()._show_license(app, args)

    def _call_prescript(self, app, args):
        return super()._call_prescript(app, args, old_version=self.old_app.version)

    def _send_information(self, app, status, value=None):
        if app > self.original_app:
            super()._send_information(app, status, value)

    def _install_packages(self, packages):
        return install_packages(packages) and dist_upgrade()

    @classmethod
    def iter_upgradable_apps(self):
        for app in Apps().get_all_locally_installed_apps():
            if ucr_is_true(app.ucr_upgrade_key):
                yield app

    def _dry_run(self, app, args):
        return self._install_packages_dry_run(app, args, with_dist_upgrade=True)
