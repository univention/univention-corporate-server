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
from os import symlink
import requests
from glob import glob
from subprocess import call
from univention.app_appliance import AppManager, get_luminance
from univention.config_registry.frontend import ucr_update


def handler(config_registry, changes):
	# query app information
	app_id = config_registry.get('umc/web/appliance/id', '')
	app = AppManager.find(app_id)
	if not app:
		return

	# query color information
	css_background = app.appliance_css_background or '#eeeeee'
	primary_color = app.appliance_primary_color or '#5a5a5a'
	secondary_color = app.appliance_secondary_color or '#7db523'
	if get_luminance(primary_color) < .5:
		theme = 'dark'
	else:
		theme = 'light'

	# adjust colors in SVG images via search and replace
	for src_path in glob('/usr/share/univention-app-appliance-branding/images/*.svg'):
		filename = os.path.basename(src_path)
		dest_path = os.path.join('/usr/share/univention-management-console-frontend/js/umc/modules/setup/', filename)
		with open(src_path, 'r') as in_file:
			with open(dest_path, 'w') as out_file:
				for line in in_file:
					out_file.write(line.replace('#ff00ff', secondary_color))

	for lang in ['', '_DE']:
		os.symlink('/var/cache/univention-appcenter/%s.README%s' % (app.component_id, lang), '/var/www/univention-management-console/js/umc/modules/appliance/appliance_first_steps.README%s' % (lang,))

	# create background image for plymouth theme
	call(['/usr/share/univention-app-appliance-branding/render-css-background', '1600x1200', css_background, '/usr/share/plymouth/themes/ucs-appliance-%s/bg.png' % theme])

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
				req = requests.get(url)
				with open(dest_path, 'wb') as handle:
					for block in req.iter_content(8192):
						handle.write(block)
				print 'Successfully downloaded %s' % url
		except (IOError, requests.HTTPError, requests.ConnectionError, requests.Timeout) as err:
			print 'WARNING: Failed to download %s' % url


	def set_grub_theme():
		if theme == 'dark':
			grub_color = 'white/black'
		elif theme == 'light':
			grub_color = 'black/white'
		ucr_update(config_registry, {
			'grub/backgroundimage':  '/usr/share/plymouth/themes/ucs-appliance-%s/bg.png' % (theme,),
			'grub/color/highlight': grub_color,
			'grub/color/normal': grub_color,
			'grub/menu/color/highlight': grub_color,
			'grub/menu/color/normal': grub_color,
			'grub/title': config_registry.get('umc/web/appliance/name', 'App') + ' Appliance'
		})

	def _svg_to_png(source, dest, params, res='800x600'):
		css_background = 'url(file:///{source}) {params}'.format(source=source, params=params)
		call(['/usr/share/univention-app-appliance-branding/render-css-background', res,  css_background, dest])

	# download image files for the app appliance
	if app.appliance_logo:
		_download(app.appliance_logo, '/usr/share/univention-management-console-frontend/js/umc/modules/setup/welcome.svg')

	if app.appliance_umc_header_logo:
		_download(app.appliance_umc_header_logo, '/usr/share/univention-management-console-frontend/js/dijit/themes/umc/images/appliance_header_logo.svg')
		_img = '/usr/share/plymouth/themes/ucs-appliance-%s/logo_header_welcome_screen.svg' % theme
		_download(app.appliance_umc_header_logo, _img)
		_params = 'no-repeat; background-size: auto 28px; background-position: left center;'
		_svg_to_png(_img, _img + '.png', _params, '400x30')
		_download(app.appliance_umc_header_logo, '/usr/share/univention-system-activation/www/css/icons/appliance_header_logo.svg')

	if app.appliance_welcome_screen_logo:
		_img = '/usr/share/plymouth/themes/ucs-appliance-%s/logo_welcome_screen.svg' % theme
		_download(app.appliance_welcome_screen_logo, _img)
		_params = 'no-repeat; background-size: contain; background-position: center center;'
		_svg_to_png(_img, _img + '.png', _params, '120x120')

	if app.appliance_bootsplash_logo:
		_img = '/usr/share/plymouth/themes/ucs-appliance-%s/logo_bootsplash.svg' % theme
		_download(app.appliance_bootsplash_logo, _img)
		_params = 'no-repeat; background-size: contain; background-position: center center;'
		_svg_to_png(_img, _img + '.png', _params)

	category_logo = app.appliance_umc_category_logo or app.appliance_welcome_screen_logo
	if category_logo:
		_download(category_logo, '/usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons/scalable/category-appliance.svg')

	# set plymouth appliance theme
	ucr_update(config_registry, {'bootsplash/theme': 'ucs-appliance-%s' % theme})
	set_grub_theme()
