#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for uninstalling an app
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

import os.path

from univention.admindiary.client import write_event
from univention.admindiary.events import APP_REMOVE_START, APP_REMOVE_SUCCESS, APP_REMOVE_FAILURE

from univention.appcenter.actions.install_base import InstallRemoveUpgrade
from univention.appcenter.ucr import ucr_save
from univention.appcenter.packages import remove_packages, remove_packages_dry_run, update_packages
from univention.appcenter.exceptions import RemoveFailed


class Remove(InstallRemoveUpgrade):

	'''Removes an application from the Univention App Center.'''
	help = 'Uninstall an app'

	prescript_ext = 'prerm'
	pre_readme = 'readme_uninstall'
	post_readme = 'readme_post_uninstall'

	def main(self, args):
		return self.do_it(args)

	def _show_license(self, app, args):
		pass

	def _do_it(self, app, args):
		self._unregister_listener(app)
		self.percentage = 5
		if not self._remove_app(app, args):
			raise RemoveFailed()
		self.percentage = 45
		self._unregister_app(app, args)
		self.percentage = 55
		self._unregister_attributes(app, args)
		self.percentage = 60
		if self._unregister_component(app):
			update_packages()
		self.percentage = 70
		self._unregister_files(app)
		self.percentage = 80
		self._call_unjoin_script(app, args)
		if not app.docker:
			ucr_save({'appcenter/prudence/docker/%s' % app.id: 'yes'})

	def _write_start_event(self, app, args):
		return write_event(APP_REMOVE_START, {'name': app.name, 'version': app.version}, username=self._get_username(args))

	def _write_success_event(self, app, context_id, args):
		return write_event(APP_REMOVE_SUCCESS, {'name': app.name, 'version': app.version}, username=self._get_username(args), context_id=context_id)

	def _write_fail_event(self, app, context_id, status, args):
		return write_event(APP_REMOVE_FAILURE, {'name': app.name, 'version': app.version, 'error_code': str(status)}, username=self._get_username(args), context_id=context_id)

	def needs_credentials(self, app):
		if os.path.exists(app.get_cache_file(self.prescript_ext)):
			return True
		return False

	def _remove_app(self, app, args):
		self._configure(app, args)
		return remove_packages(app.get_packages(additional=False))

	def _dry_run(self, app, args):
		return remove_packages_dry_run(app.get_packages(additional=False))
