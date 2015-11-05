#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for updating the list of available apps
#  (UMC version)
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

import os
import os.path
from glob import glob
import shutil
import stat

from univention.config_registry import handler_commit

from univention.appcenter.actions.update import Update
from univention.appcenter.log import catch_stdout
from univention.appcenter.app import AppManager

FRONTEND_ICONS_DIR = '/usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons/scalable'


class Update(Update):
	def _update_local_files(self):
		self.debug('Updating app icon files in UMC directory...')

		# some variables could change apps.xml
		# e.g. Name, Description
		self._update_conffiles()

		# clear existing SVG logo files and re-copy them again
		for isvg in glob(os.path.join(FRONTEND_ICONS_DIR, 'apps-*.svg')):
			os.unlink(isvg)

		for app in AppManager.get_all_apps():
			for _app in AppManager.get_all_apps_with_id(app.id):
				self._update_svg_file(_app.logo_name, _app.get_cache_file('logo'))
				self._update_svg_file(_app.logo_detail_page_name, _app.get_cache_file('logodetailpage'))

	def _update_conffiles(self):
		with catch_stdout(self.logger):
			handler_commit(['/usr/share/univention-management-console/modules/apps.xml', '/usr/share/univention-management-console/i18n/de/apps.mo'])

	def _update_svg_file(self, _dest_file, src_file):
		if not _dest_file:
			return
		dest_file = os.path.join(FRONTEND_ICONS_DIR, _dest_file)
		if os.path.exists(src_file):
			shutil.copy2(src_file, dest_file)
			self.debug('copying %s -> %s' % (src_file, dest_file))

			# images are created with UMC umask: -rw-------
			# change the mode to UCS umask:      -rw-r--r--
			os.chmod(dest_file, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IROTH)
