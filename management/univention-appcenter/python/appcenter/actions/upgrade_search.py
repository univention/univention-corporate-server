#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for searching for available upgrading
#
# Copyright 2015 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.
#

from univention.config_registry import ConfigRegistry
from univention.config_registry.frontend import ucr_update

from univention.appcenter.app import AppManager
from univention.appcenter.actions import UniventionAppAction, StoreAppAction


class UpgradeSearch(UniventionAppAction):
	'''Searches for available upgrades of apps.'''
	help = 'Searches for upgrades'

	def setup_parser(self, parser):
		parser.add_argument('app', nargs='*', action=StoreAppAction, help='The ID of the application')

	def main(self, args):
		from univention.appcenter import get_action
		get_action('update').call()
		apps = args.app
		if not apps:
			apps = AppManager.get_all_locally_installed_apps()
		ucr = ConfigRegistry()
		for app in apps:
			self.debug('Checking %s' % app)
			if not app.is_installed():
				continue
			upgrade_available = self._check_for_upgrades(app)
			if upgrade_available is True:
				ucr_update(ucr, {app.ucr_upgrade_key: 'yes'})
			elif upgrade_available is False:
				ucr_update(ucr, {app.ucr_upgrade_key: None})
		ucr = ConfigRegistry()
		ucr.load()
		return any(ucr.is_true(app.ucr_upgrade_key) for app in apps)

	def _check_for_upgrades(self, app):
		return AppManager.find(app.id, latest=True) > app
