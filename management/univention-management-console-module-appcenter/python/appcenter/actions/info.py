#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module showing information about the App Center
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

from json import dumps

from univention.config_registry import ConfigRegistry

from univention.appcenter.actions import UniventionAppAction, get_action
from univention.appcenter.app import AppManager


class Info(UniventionAppAction):
	'''Shows information on the current state of the App Center itself.'''
	help = 'Show general info'

	def setup_parser(self, parser):
		parser.add_argument('--as-json', action='store_true', help='Output in a machine readable format')

	def main(self, args):
		if args.as_json:
			self._as_json()
		else:
			self._output()

	def _as_json(self):
		installed = [str(app) for app in self.get_installed_apps()]
		upgradable = [app.id for app in self.get_upgradable_apps()]
		ret = {'ucs': self.get_ucs_version(), 'compat': self.get_compatibility(), 'installed': installed, 'upgradable': upgradable}
		self.log(dumps(ret))
		return ret

	def _output(self):
		self.log('UCS: %s' % self.get_ucs_version())
		self.log('App Center compatibility: %s' % self.get_compatibility())
		self.log('Installed: %s' % ' '.join(str(app) for app in self.get_installed_apps()))
		self.log('Upgradable: %s' % ' '.join(app.id for app in self.get_upgradable_apps()))

	def get_ucs_version(self):
		ucr = ConfigRegistry()
		ucr.load()
		return '%s-%s errata%s' % (ucr.get('version/version'), ucr.get('version/patchlevel'), ucr.get('version/erratalevel'))

	@classmethod
	def get_compatibility(cls):
		''' Returns the version number of the App Center.
		As App Center within a domain may talk to each other it is necessary
		to ask whether they are compatible.
		The version number will rise whenever a change was made that may break compatibility.

		1: initial app center 12/12 (not assigned, appcenter/version was not supported)
		2: app center with remote installation 02/13 (not assigned, appcenter/version was not supported)
		3: app center with version and only_dry_run 03/13
		4: app center with docker support and new App class 11/15
		'''
		return 4

	def get_installed_apps(self):
		return AppManager.get_all_locally_installed_apps()

	def get_upgradable_apps(self):
		upgrade = get_action('upgrade')
		return list(upgrade.iter_upgradable_apps())
