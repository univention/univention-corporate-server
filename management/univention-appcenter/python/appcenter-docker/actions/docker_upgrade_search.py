#!/usr/bin/python3
#
# Univention App Center
#  univention-app module for searching for available upgrading
#  (docker version)
#
# SPDX-FileCopyrightText: 2015-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

from univention.appcenter.actions.docker_base import DockerActionMixin
from univention.appcenter.actions.upgrade_search import UpgradeSearch


class UpgradeSearch(UpgradeSearch, DockerActionMixin):

    def _check_for_upgrades(self, app):
        upgrade_available = super()._check_for_upgrades(app)
        docker = self._get_docker(app)
        if not docker:
            return upgrade_available
        if not docker.is_running():
            self.log('%s: Not running, cannot check further' % app)
            return upgrade_available or None
        result = self._execute_container_script(app, 'update_available', credentials=False, output=True)
        if result is not None:
            process, log = result
            if process.returncode != 0:
                self.fatal('%s: Searching for App upgrade failed!' % app)
                return upgrade_available or None
            output = '\n'.join(log.stdout())
            if output:
                output = output.strip()
            if output:
                self.log('%s: Update available: %s' % (app, output))
                return True
        return upgrade_available
