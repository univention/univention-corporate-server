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

from univention.config_registry import handler_commit

from univention.appcenter.actions.update import Update

FRONTEND_ICONS_DIR = '/usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons'


class Update(Update):
	def _process_new_file_png(self, filename, local_app):
		component, ext = os.path.splitext(os.path.basename(filename))
		png_50 = os.path.join(FRONTEND_ICONS_DIR, '50x50', 'apps-%s.png' % component)
		shutil.copy2(filename, png_50)

	def _update_local_files(self):
		# some variables could change apps.xml
		# e.g. Name, Description
		self._update_conffiles()

		# special handling for icons
		for png in glob(os.path.join(FRONTEND_ICONS_DIR, '**', 'apps-*.png')):
			os.unlink(png)

	def _update_conffiles(self):
		handler_commit(['/usr/share/univention-management-console/modules/apps.xml', '/usr/share/univention-management-console/i18n/de/apps.mo'])
