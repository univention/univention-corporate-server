#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for searching for available upgrading
#  (docker version)
#
# Copyright 2015-2019 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.
#

from univention.appcenter.actions.upgrade_search import UpgradeSearch
from univention.appcenter.actions.docker_base import DockerActionMixin


class UpgradeSearch(UpgradeSearch, DockerActionMixin):

	def _check_for_upgrades(self, app):
		upgrade_available = super(UpgradeSearch, self)._check_for_upgrades(app)
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
