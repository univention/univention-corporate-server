#!/usr/bin/python3
#
# Univention App Center
#  univention-app module for getting log output from a docker app
#
# SPDX-FileCopyrightText: 2015-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import subprocess

from univention.appcenter.actions import StoreAppAction, UniventionAppAction
from univention.appcenter.actions.docker_base import DockerActionMixin


class Logs(UniventionAppAction, DockerActionMixin):
    """Get log output of an app."""

    help = 'Get log output of an app.'

    def setup_parser(self, parser):
        parser.add_argument('app', action=StoreAppAction, help='The ID of the App whose logs shall be output')

    def main(self, args):
        if not args.app.docker or not args.app.is_installed():
            self.log('ERROR: Currently the logs command only works for installed docker apps.')
            return

        return self.show_docker_logs(args)

    def show_docker_logs(self, args):
        docker = self._get_docker(args.app)
        self.log(f"#### 'docker logs {docker.container}' output:")
        return subprocess.call(['docker', 'logs', docker.container])
