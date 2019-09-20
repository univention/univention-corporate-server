#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for listing all apps
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

import re
from fnmatch import fnmatch

from univention.appcenter.actions import UniventionAppAction
from univention.appcenter.app_cache import Apps
from univention.appcenter.udm import get_app_ldap_object, get_machine_connection
from univention.appcenter.utils import flatten
from univention.appcenter.ucr import ucr_get, ucr_is_true


class List(UniventionAppAction):

	'''Lists all available apps; shows installed version.'''
	help = 'List all apps'

	def setup_parser(self, parser):
		parser.add_argument('app', nargs='?', help='The ID of the App that shall be listed. May contain asterisk. Default: list all apps')
		parser.add_argument('--with-repository', action='store_true', help='Also list the repository name')
		parser.add_argument('--ids-only', action='store_true', help='Only list the IDs. Does not respect APP argument')

	def main(self, args):
		first = True
		if args.ids_only:
			for app in self.get_apps():
				self.log('%s' % app.id)
			return
		for app, versions, installations in self._list(args.app):
			if not first:
				self.log('')
			self.log('%s' % app.id)
			self.log('  Name: %s' % app.name)
			if args.with_repository:
				self.log('  Repository: %s' % app.component_id)
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

	@classmethod
	def get_apps(cls):
		ret = []
		apps = Apps().get_all_apps()
		blacklist = ucr_get('repository/app_center/blacklist')
		whitelist = ucr_get('repository/app_center/whitelist')
		if blacklist:
			blacklist = re.split('\s*,\s*', blacklist)
		if whitelist:
			whitelist = re.split('\s*,\s*', whitelist)
		for app in apps:
			if blacklist or whitelist:
				unlocalised_app = app.get_app_cache_obj().copy(locale='en').find_by_component_id(app.component_id)
				if cls._blacklist_includes_app(blacklist, unlocalised_app) and not cls._blacklist_includes_app(whitelist, unlocalised_app):
					continue
			if app.end_of_life and not app.is_installed():
				continue
			if ucr_is_true('ad/member') and app.ad_member_issue_hide:
				continue
			if ucr_get('server/role') not in app.server_role:
				continue
			docker_prudence = app._docker_prudence_is_true()
			install_permissions = app.install_permissions_exist()
			if docker_prudence or not install_permissions:
				_apps = Apps().get_all_apps_with_id(app.id)
				if docker_prudence:
					_apps = [_app for _app in _apps if _app.docker_migration_works or not _app.docker]
				if not install_permissions:
					_apps = [_app for _app in _apps if not _app.install_permissions] or _apps
				try:
					app = sorted(_apps)[-1]
				except IndexError:
					continue
			ret.append(app)
		return ret

	@classmethod
	def _blacklist_includes_app(cls, the_list, app):
		if not the_list:
			return False
		if '*' in the_list:
			return True
		the_list = [item.lower() for item in the_list]
		if app.id.lower() in the_list:
			return True
		if app.name.lower() in the_list:
			return True
		if any(category.lower() in the_list for category in app.categories):
			return True
		return False

	def _list(self, pattern):
		ret = []
		lo, pos = get_machine_connection()
		for app in self.get_apps():
			versions = []
			installations = {}
			if pattern:
				if not fnmatch(app.id, pattern):
					continue
			app = Apps().find(app.id, latest=True)
			for _app in Apps().get_all_apps_with_id(app.id):
				ldap_obj = get_app_ldap_object(_app, lo, pos)
				servers = ldap_obj.installed_on_servers()
				versions.append(_app.version)
				installations[_app.version] = servers
			ret.append((app, versions, installations))
		return ret
