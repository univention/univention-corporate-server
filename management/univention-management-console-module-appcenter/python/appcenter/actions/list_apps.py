#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for listing all apps
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

from fnmatch import fnmatch

from univention.appcenter.actions import UniventionAppAction
from univention.appcenter.app import AppManager
from univention.appcenter.udm import get_app_ldap_object
from univention.appcenter.utils import flatten

class List(UniventionAppAction):
	'''Lists all available apps; shows installed version.'''
	help='List all app'

	def setup_parser(self, parser):
		parser.add_argument('app', nargs='?', help='The ID of the app that shall be listed. May contain asterisk. Default: list all apps')

	def main(self, args):
		first = True
		for app, versions, installations in self._list(args.app):
			if not first:
				self.log('')
			self.log('%s' % app.id)
			self.log('  Name: %s' % app.name)
			if args.app:
				self.log('  Versions:')
				for version in versions:
					self.log('    %s' % version)
					version_installations = installations.get(version)
					if version_installations:
						self.log('      Installed: %s' % ' '.join(sorted(version_installations)))
			else:
				self.log('  Latest version: %s' % app.version)
				self.log('  Installations: %s' % ' '.join(sorted(flatten(installations.values()))))
			first = False

	def _list(self, pattern):
		ret = []
		for app in AppManager.get_all_apps():
			versions = []
			installations = {}
			if pattern:
				if not fnmatch(app.id, pattern):
					continue
			app = AppManager.find(app, latest=True)
			for _app in AppManager.get_all_apps_with_id(app.id):
				ldap_obj = get_app_ldap_object(_app)
				servers = ldap_obj.installed_on_servers()
				versions.append(_app.version)
				installations[_app.version] = servers
			ret.append((app, versions, installations))
		return ret

