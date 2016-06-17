#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Appliance Branding
#   UCR module template for setting up a new app branding
#
# Copyright 2016 Univention GmbH
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

import os.path
from glob import glob
from subprocess import call
from univention.appcenter.app import AppManager

def handler(config_registry, changes):
	# query app information
	app_id = config_registry.get('umc/web/appliance/id', '')
	app = AppManager.find(app_id)
	if not app:
		return

	# query color information
	css_background = app.appliance_css_background or '#eeeeee'
	primary_color = '#' + (app.appliance_primary_color or '5a5a5a')
	secondary_color = '#' + (app.appliance_secondary_color or '7db523')

	# adjust colors in SVG images via search and replace
	for src_path in glob('/usr/share/univention-app-appliance-branding/images/*.svg'):
		filename = os.path.basename(src_path)
		dest_path = os.path.join('/usr/share/univention-management-console-frontend/js/umc/modules/setup/', filename)
		with open(src_path, 'r') as in_file:
			with open(dest_path, 'w') as out_file:
				for line in in_file:
					out_file.write(line.replace('#ff00ff', secondary_color))

	# create background image for plymout theme
	call(['/usr/share/univention-app-appliance-branding/render-css-background', '1600x1200', css_background, '/usr/share/plymouth/themes/ucs-appliance/bg.png'])



