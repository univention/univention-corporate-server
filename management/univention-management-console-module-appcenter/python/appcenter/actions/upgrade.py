#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for upgrading an app
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

from univention.appcenter.app import AppManager
from univention.appcenter.actions.install import Install

class Upgrade(Install):
	'''Upgrades an installed application from the Univention App Center.'''
	help='Upgrade an app'

	pre_readme = 'readme_update'
	post_readme = 'readme_post_update'

	def __init__(self):
		super(Upgrade, self).__init__()
		self.old_app = None

	def setup_parser(self, parser):
		super(Install, self).setup_parser(parser)

	def _app_too_old(self, current_app, specified_app):
		if current_app >= specified_app:
			self.fatal('A newer version of %s than the one installed must be present and chosen' % specified_app.id)
			return True
		return False

	def main(self, args):
		app = args.app
		self.old_app = AppManager.find(app)
		if app == self.old_app:
			app = AppManager.find(app, latest=True)
		if self._app_too_old(self.old_app, app):
			return
		args.app = app
		self.do_it(args)

	def _install_only_master_packages(self, args):
		return False

	def _revert(self, app, args):
		try:
			self.log('Trying to revert to old version. This may lead to problems, but it is better than leaving it the way it is now')
			self._do_it(self.old_app, args)
		except Exception:
			pass

	def _show_license(self, app, args):
		if app.license_agreement != self.old_app.license_agreement:
			return super(Upgrade, self)._show_license(app, args)

	def _call_prescript(self, app):
		return super(Upgrade, self)._call_prescript(app, old_version=self.old_app.version)

	def _send_information(self, app, status):
		if app > self.old_app:
			super(Upgrade, self)._send_information(app, status)

