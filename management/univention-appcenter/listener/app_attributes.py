#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  app attributes listener
#
# Copyright 2019 Univention GmbH
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

from __future__ import absolute_import

import os
import os.path
import json
import shutil

from ldap.dn import dn2str, str2dn

import univention.debug

from univention.listener.handler import ListenerModuleHandler
from univention.appcenter.app_cache import AllApps
from univention.appcenter.udm import search_objects

name = 'app_attributes'

FNAME = '/var/lib/univention-appcenter/attributes/mapping.json'
class AppAttributes(ListenerModuleHandler):
	def initialize(self):
		dirname = os.path.dirname(FNAME)
		if os.path.exists(dirname):
			return
		with self.as_root():
			os.makedirs(dirname)

	def _write_json_without_some_debug_output(self):
		# otherwise UDM lib unintentionally clutters the log file. univention.debug opened a
		# file handle to listener.log in the listener itself and this is used in every
		# listener module
		univention.debug.set_function(univention.debug.NO_FUNCTION)
		try:
			self._write_json()
		finally:
			univention.debug.set_function(univention.debug.FUNCTION)

	def _write_json(self):
		self.logger.info('Gathering AppAttributes...')
		locales = [locale.split('.')[0] for locale in self.ucr.get('locale', 'en_US.UTF-8:UTF-8').split() if '.' in locale]
		if 'en_US' not in locales:
			locales.append('en_US')
		cache = {}
		custom_attributes_base = 'cn=custom attributes,cn=univention,%s' % self.ucr.get('ldap/base')
		for current_locale in locales:
			locale_cache = cache[current_locale] = {}
			app_objs = search_objects('appcenter/app', self.lo, self.po)
			apps = {}
			for app_obj in app_objs:
				app_version = app_obj['version']
				app_id = app_obj['id'][:-len(app_version) - 1]
				app = AllApps().find(app_id, app_version=app_version)
				if app:
					if app.id in apps:
						if apps[app.id] > app:
							continue
					apps[app.id] = app
			for app in apps.itervalues():
				for attribute in app.umc_options_attributes:
					attribute, option_name = (attribute.split(':', 1) * 2)[:2]
					objs = search_objects('settings/extended_attribute', self.lo, self.po, custom_attributes_base, CLIName=attribute)
					for obj in objs:
						for module in obj['module']:
							if search_objects('settings/extended_options', self.lo, self.po, custom_attributes_base, objectClass=obj['objectClass'], module=module):
								# a newer version of the App is installed that uses the
								# superior settings/extended_option
								continue
							if module not in locale_cache:
								locale_cache[module] = {}
							option_def = locale_cache[module]
							group_name = obj['groupName']
							for loc, desc in obj['translationGroupName']:
								if loc == current_locale:
									group_name = desc
									break
							tab_name = obj['tabName']
							for loc, desc in obj['translationTabName']:
								if loc == current_locale:
									tab_name = desc
									break
							short_description = obj['shortDescription']
							for loc, desc in obj['translationShortDescription']:
								if loc == current_locale:
									short_description = desc
									break
							if obj['syntax'] == 'boolean':
								boolean_values = ['1', '0']
							elif obj['syntax'] in ['TrueFalseUp', 'TrueFalseUpper']:
								boolean_values = ['TRUE', 'FALSE']
							elif obj['syntax'] == 'TrueFalse':
								boolean_values = ['true', 'false']
							elif obj['syntax'] == 'OkOrNot':
								boolean_values = ['OK', 'Not']
							else:
								continue
							default = int(obj['default'] == boolean_values[0])
							attributes = []
							layout = []
							option_def[option_name] = {
								'label': group_name or tab_name,
								'description': short_description,
								'default': default,
								'boolean_values': boolean_values,
								'attributes': attributes,
								'layout': layout,
								'attribute_name': obj['CLIName'],
							}
							base = dn2str(str2dn(obj.dn)[1:])
							for _obj in search_objects('settings/extended_attribute', self.lo, self.po, base, univentionUDMPropertyModule=module):
								if obj.dn == _obj.dn:
									continue
								if _obj['disableUDMWeb'] == '1':
									continue
								attributes.append(_obj['CLIName'])
								if _obj['tabAdvanced']:
									group_name = _obj['tabName']
									for loc, desc in _obj['translationTabName']:
										if loc == current_locale:
											group_name = desc
											break
									group_position = _obj['tabPosition']
								else:
									group_name = _obj['groupName']
									for loc, desc in _obj['translationGroupName']:
										if loc == current_locale:
											group_name = desc
											break
									group_position = _obj['groupPosition']
								for group in layout:
									if group['label'] == group_name:
										break
								else:
									group = {
										'label': group_name,
										'description': '',
										'advanced': False,
										'is_app_tab': False,
										'layout': [],
										'unsorted': [],
									}
									layout.append(group)
								group_layout = group['layout']
								if group_position:
									group_position = int(group_position)
									while len(group_layout) < group_position:
										group_layout.append([])
									group_layout[group_position - 1].append(_obj['CLIName'])
								else:
									group['unsorted'].append(_obj['CLIName'])
							for group in layout:
								unsorted = group.pop('unsorted')
								if unsorted:
									group['layout'].append(unsorted)
		self.logger.info('Finished')
		tmp_fname = FNAME + '.tmp'
		with open(tmp_fname, 'w') as fd:
			json.dump(cache, fd)
		shutil.move(tmp_fname, FNAME)

	def create(self, dn, new):
		with self.as_root():
			self._write_json_without_some_debug_output()

	def modify(self, dn, old, new, old_dn):
		with self.as_root():
			self._write_json_without_some_debug_output()

	def remove(self, dn, old):
		with self.as_root():
			self._write_json_without_some_debug_output()

	class Configuration(ListenerModuleHandler.Configuration):
		name = name
		ldap_filter = '(|(univentionObjectType=settings/extended_attribute)(univentionObjectType=settings/extended_option)(univentionObjectType=appcenter/app))'
		description = 'Writes a JSON file with information about installed Apps for the UMC UDM module to load'
