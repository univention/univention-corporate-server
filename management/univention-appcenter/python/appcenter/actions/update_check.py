#!/usr/bin/python3
#
# Univention App Center
#  univention-app module checking UCS update regarding installed apps
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2021-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
from argparse import Action
from tempfile import TemporaryDirectory

from univention.appcenter.actions import UniventionAppAction, get_action
from univention.appcenter.app_cache import AppCenterCache, Apps, default_server
from univention.appcenter.log import get_logfile_logger
from univention.appcenter.ucr import ucr_get
from univention.lib.ucs import UCS_Version


class CheckUcsVersion(Action):
    def __call__(self, parser, namespace, value, option_string=None):
        try:
            UCS_Version(value + '-0')
        except ValueError as exc:
            parser.error('--ucs-version ' + str(exc))
        setattr(namespace, self.dest, value)


class UpdateCheck(UniventionAppAction):
    """
    Check if update to next ucs minor version is possible with the
    locally installed apps

    For docker apps check if is available in next UCS version.
    For package based apps check if there is an app version with the same
    component in the next UCS version
    """

    help = 'Check for all locally installed Apps if they are available in the next UCS version'

    def setup_parser(self, parser):
        parser.add_argument(
            '--ucs-version',
            action=CheckUcsVersion,
            required=True,
            help="the next ucs version (MAJOR.MINOR), check if update with locally installed apps is possible",
        )

    @classmethod
    def app_can_update(cls, app, next_version, next_apps):
        """
        checks if update is possible for this app
        docker apps have to support the next version
        components must be available in the next version
        component id of package based app must be available in the next version
        """
        if app.docker:
            # current docker must support next version
            if next_version in app.supported_ucs_versions:
                return True
        else:
            if app.without_repository:
                # current component must be available in next version
                for a in next_apps:
                    if a.id == app.id:
                        return True
            else:
                # current component id must be available in next version
                for a in next_apps:
                    if a.component_id == app.component_id:
                        return True
        return False

    @classmethod
    def get_blocking_apps(cls, ucs_version):
        """checks if update is possible for this app"""
        ucs_version = UCS_Version(ucs_version + '-0')
        next_minor = '%(major)d.%(minor)d' % ucs_version
        next_version = '%(major)d.%(minor)d-%(patchlevel)d' % ucs_version
        current_version = UCS_Version(ucr_get('version/version') + '-0')
        current_minor = '%(major)d.%(minor)d' % current_version

        # if this is just a patchlevel update, everything is fine
        if current_minor >= next_minor:
            return {}

        # first, update the local cache and get current apps
        update = get_action('update')
        update.logger = get_logfile_logger('update-check')
        update.call()
        current_cache = Apps(ucs_version=current_minor, locale='en')

        # get apps in next version
        with TemporaryDirectory() as tempdir:
            update.call(ucs_version=next_minor, cache_dir=os.path.join(tempdir, next_minor), just_get_cache=True)
            next_cache = AppCenterCache.build(ucs_versions=[next_minor], server=default_server(), locale='en', cache_dir=tempdir)
            next_apps = next_cache.get_every_single_app()

        # check apps
        blocking_apps = {}
        for app in current_cache.get_all_locally_installed_apps():
            if not cls.app_can_update(app, next_version, next_apps):
                cls.debug('app %s is not available for %s' % (app.id, next_version))
                blocking_apps[app.component_id] = app.name
            else:
                cls.debug('app %s is available for %s' % (app.id, next_version))
        return blocking_apps

    def main(self, args):
        blocking_apps = self.get_blocking_apps(args.ucs_version)
        if blocking_apps:
            self.log('The update to %s is currently not possible,' % args.ucs_version)
            self.log('because the following Apps are not available for UCS %s:' % args.ucs_version)
            for app in blocking_apps.values():
                self.log(' * %s' % app)
            return 1
