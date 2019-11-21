#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Appliance
#  Application class
#
# Copyright 2016-2019 Univention GmbH
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

import univention.appcenter.app as app
import univention.appcenter.app_cache as app_cache
import struct
import os
import json


class App(app.App):
	appliance_name = app.AppAttribute()

	# UMC modules to be displayed in the UMC category 'favorites'
	appliance_favorite_modules = app.AppListAttribute()

	# simple two-color scheme for setup wizard + system activation
	appliance_primary_color = app.AppAttribute()
	appliance_secondary_color = app.AppAttribute()

	# background CSS style as well as logo for the bootsplash screen
	appliance_css_background = app.AppAttribute()
	appliance_bootsplash_logo = app.AppAttribute()

	# additional logos for the setup wizard
	appliance_umc_header_logo = app.AppAttribute()  # also used for the system activation
	appliance_logo = app.AppAttribute()  # logo is displayed on the first wizard page

	# logo and font color to be used together with the appliance_css_background
	# for the welcome screen
	appliance_welcome_screen_logo = app.AppAttribute()
	appliance_welcome_screen_font_color = app.AppAttribute()

	# properties to be applied to the portal
	appliance_portal_logo = app.AppAttribute()
	appliance_portal_font_color = app.AppAttribute()
	appliance_portal_css_background = app.AppAttribute()
	appliance_portal_background_image = app.AppAttribute()
	appliance_portal_title = app.AppAttribute()
	readme_appliance = app.AppFileAttribute()

	# additional properties
	appliance_pages_blacklist = app.AppAttribute()
	appliance_fields_blacklist = app.AppAttribute()
	appliance_blacklist = app.AppAttribute()
	appliance_whitelist = app.AppAttribute()
	appliance_allow_preconfigured_setup = app.AppBooleanAttribute(default=False)


class AppCache(app_cache.AppCache):
	def get_app_class(self):
		if self._app_class is None:
			self._app_class = App
		return self._app_class


class AppCenterCache(app_cache.AppCenterCache):
	def get_app_cache_class(self):
		if self._cache_class is None:
			self._cache_class = AppCache
		return self._cache_class


class Apps(app_cache.Apps):
	def get_appcenter_cache_class(self):
		if self._cache_class is None:
			self._cache_class = AppCenterCache
		return self._cache_class


def get_luminance(hexcolor):
	hexcolor = hexcolor.strip(' #')
	red, green, blue = struct.unpack('BBB', hexcolor.decode('hex'))
	# Taken from: http://stackoverflow.com/questions/1855884/determine-font-color-based-on-background-color
	return (0.299 * red + 0.587 * green + 0.114 * blue) / 255


def get_cache_dir_name(app):
	CACHE_DIR = '/var/cache/univention-app-appliance/'
	app_cache_dir = os.path.join(CACHE_DIR, app.id)
	return app_cache_dir


def get_app_style_properties(app):
	local_cache_name = 'app_props' if app.get_locale() == 'en' else 'app_props_de'
	try:
		with open(os.path.join(get_cache_dir_name(app), local_cache_name)) as fd:
			props = json.load(fd)
			print('Properties loaded from %s cache' % local_cache_name)
			return props
	except Exception as exc:
		if not os.path.exists(os.path.join(get_cache_dir_name(app), local_cache_name)):
			print('Properties loaded from web for %s' % local_cache_name)
		else:
			print('Warning: ' + exc)

	props = dict()
	for i in (
		'primary_color',
		'secondary_color',
		'css_background',
		'bootsplash_logo',
		'umc_header_logo',
		'logo',
		'welcome_screen_logo',
		'welcome_screen_font_color',
		'favorite_modules',
		'portal_logo',
		'portal_font_color',
		'portal_css_background',
		'portal_background_image',
		'portal_title',
	):
		ival = getattr(app, 'appliance_%s' % i, None)
		if ival:
			props[i] = ival
	return props
