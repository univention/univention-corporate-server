#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Appliance Branding
#  Application class
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
#

import univention.appcenter.app as app
import struct

class App(app.App):
	appliance_category_modules = app.AppListAttribute()
	appliance_primary_color = app.AppAttribute()
	appliance_secondary_color = app.AppAttribute()
	appliance_css_background = app.AppAttribute()
	appliance_bootsplash_logo = app.AppAttribute()
	appliance_umc_header_logo = app.AppAttribute()
	appliance_welcome_screen_logo = app.AppAttribute()
	appliance_logo = app.AppAttribute()
	appliance_links = app.AppAttribute()

class AppManager(app.AppManager):
	_AppClass = App
	_cache = []
	_cache_file = None

def get_luminance(hexcolor):
	hexcolor = hexcolor.strip(' #')
	red, green, blue = struct.unpack('BBB', hexcolor.decode('hex'))
	# Taken from: http://stackoverflow.com/questions/1855884/determine-font-color-based-on-background-color
	return (0.299 * red + 0.587 * green + 0.114 * blue) / 255;

