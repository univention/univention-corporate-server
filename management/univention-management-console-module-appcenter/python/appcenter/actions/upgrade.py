#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for installing an app
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

from univention.appcenter.actions.install import Install

class Upgrade(Install):
	def _send_as_function(self):
		return 'update'

	def setup_parser(self, parser):
		super(Upgrade, self).setup_parser(parser)
		parser.add_argument('--all', help='Upgrade all apps that can be upgraded.')

	def _show_license(self, app, args):
		if app.get('licenseagreement') != app.candidate.get('licenseagreement'):
			return super(Upgrade, self)._show_license(app.candidate, args)
		else:
			# nothing new to show
			return True

	def _show_readme_install(self, app, args):
		self._show_file(app.candidate, 'readmeupdate', args, confirm=True)

	def _show_readme_postinstall(self, app, args):
		self._show_file(app.candidate, 'readmepostupdate', args, confirm=True)

	@classmethod
	def iter_upgradable_apps(cls):
		from univention.management.console.modules.appcenter.app_center import Application as _Application
		package_manager = cls._get_package_manager()
		for app in _Application.all_installed(package_manager):
			if app.candidate:
				yield app

