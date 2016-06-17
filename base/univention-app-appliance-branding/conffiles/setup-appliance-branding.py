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
import urllib
import requests
from glob import glob
from subprocess import call
from univention.app_appliance import AppManager
from univention.config_registry.frontend import ucr_update


def get_plymouth_theme(hexcolor):
	red = int(hexcolor[2:4], 16)
	green = int(hexcolor[4:6], 16)
	blue = int(hexcolor[6:8], 16)
	# Taken from: http://stackoverflow.com/questions/1855884/determine-font-color-based-on-background-color
	perceptive_luminance = 1 - ( 0.299 * red + 0.587 * green + 0.114 * blue)/255;
	if perceptive_luminance < .5:
		return 'light'
	else:
		return 'dark'


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
	plymouth_theme = get_plymouth_theme(primary_color)

	# adjust colors in SVG images via search and replace
	for src_path in glob('/usr/share/univention-app-appliance-branding/images/*.svg'):
		filename = os.path.basename(src_path)
		dest_path = os.path.join('/usr/share/univention-management-console-frontend/js/umc/modules/setup/', filename)
		with open(src_path, 'r') as in_file:
			with open(dest_path, 'w') as out_file:
				for line in in_file:
					out_file.write(line.replace('#ff00ff', secondary_color))

	# create background image for plymouth theme
	call(['/usr/share/univention-app-appliance-branding/render-css-background', '1600x1200', css_background, '/usr/share/plymouth/themes/ucs-appliance-%s/bg.png' % plymouth_theme])

	def _download(filename, dest_path):
		url = 'https://{server}/meta-inf/{version}/{app}/{file}'.format(
			server=config_registry.get('repository/app_center/server'),
			version=config_registry.get('version/version'),
			app=app.id,
			file=filename,
		)
		try:
			req = requests.head(url, timeout=5)
			if req.status_code < 400:
				urllib.urlretrieve(url, dest_path)
				print 'Successfully downloaded %s' % url
		except (IOError, requests.HTTPError, requests.ConnectionError, requests.Timeout) as err:
			print 'WARNING: Failed to download %s' % url

	
	def set_grub_theme():
		if plymouth_theme == 'dark':
			grub_color = 'white/black'
		elif plymouth_theme == 'light':
			grub_color = 'black/white'
		ucr_update(config_registry, {
			'grub/backgroundimage':  '/usr/share/plymouth/themes/ucs-appliance-%s/bg.png' % (plymouth_theme,),
			'grub/color/highlight': grub_color,
			'grub/color/normal': grub_color,
			'grub/menu/color/highlight': grub_color,
			'grub/menu/color/normal': grub_color,
			'grub/title': config_registry.get('umc/web/appliance/name', 'App') + ' Appliance'
		})
	
	# download image files for the app appliance
	if app.appliance_logo:
		_download(app.appliance_logo, '/usr/share/univention-management-console-frontend/js/umc/modules/setup/welcome.svg')
	if app.appliance_umc_header_logo:
		_stem, _ext = os.path.splitext(app.appliance_umc_header_logo)
		_download(app.appliance_umc_header_logo, '/usr/share/univention-management-console-frontend/js/dijit/themes/umc/images/appliance_header_logo%s' % _ext)
	if app.appliance_welcome_screen_logo:
		_stem, _ext = os.path.splitext(app.appliance_welcome_screen_logo)
		_download(app.appliance_welcome_screen_logo, '/usr/share/plymouth/themes/ucs-appliance-%s/logo_welcome_screen%s' % (plymouth_theme, _ext))
	if app.appliance_bootsplash_logo:
		_stem, _ext = os.path.splitext(app.appliance_bootsplash_logo)
		_download(app.appliance_bootsplash_logo, '/usr/share/plymouth/themes/ucs-appliance-%s/logo_bootsplash%s' % (plymouth_theme, _ext))

	# set plymouth appliance theme
	ucr_update(config_registry, {'bootsplash/theme': 'ucs-appliance-%s' % plymouth_theme})
	set_grub_theme()
