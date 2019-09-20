#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for getting app meta information
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

from pipes import quote
import re
from argparse import Action
from fnmatch import translate
from ConfigParser import NoOptionError, NoSectionError

from univention.appcenter.app import CaseSensitiveConfigParser
from univention.appcenter.app_cache import Apps
from univention.appcenter.utils import shell_safe
from univention.appcenter.actions import UniventionAppAction, StoreAppAction
from univention.appcenter.ucr import ucr_get


class StoreKeysAction(Action):

	def __call__(self, parser, namespace, value, option_string=None):
		keys = []
		for val in value:
			try:
				section, key = val.rsplit(':', 1)
			except:
				section, key = None, val
			keys.append((section, key))
		setattr(namespace, self.dest, keys)


def _match(value, pattern):
	regex = re.compile(translate(pattern), re.I)
	return regex.match(value)


class Get(UniventionAppAction):

	'''Fetches meta information about the app.'''
	help = 'Query an app'

	def setup_parser(self, parser):
		parser.add_argument('app', action=StoreAppAction, help='The ID of the App that shall be queried')
		parser.add_argument('--shell', action='store_true', help='Print the information so that it can be evaluated in shell scripts. Example: %(prog)s app Vendor UseShop -> vendor="Vendor Inc."\\nuse_shop="1"')
		parser.add_argument('--values-only', action='store_true', help='Only print the value of KEY, not KEY itself')
		parser.add_argument('keys', action=StoreKeysAction, metavar='KEY', nargs='+', help='The key of the meta information')

	def main(self, args):
		for section, key, value in self.get_values(args.app, args.keys):
			if args.shell:
				if isinstance(value, list):
					value = ' '.join(value)
				if isinstance(value, bool):
					value = int(value)
				if value is None:
					value = ''
				value = str(value)
				if args.values_only:
					self.log(value)
				else:
					if section is not None:
						key = '%s__%s' % (section, key)
					self.log('%s=%s' % (shell_safe(key), quote(value)))
			else:
				if isinstance(value, list):
					value = ', '.join(value)
				if section is not None:
					key = '%s/%s' % (section, key)
				if args.values_only:
					self.log(value)
				else:
					self.log('%s: %s' % (key, value))

	@classmethod
	def to_dict(cls, app):
		ret = app.attrs_dict()
		ret['logo_name'] = app.logo_name
		ret['logo_detail_page_name'] = app.logo_detail_page_name
		ret['license_description'] = app.license_description
		ret['thumbnails'] = app.get_thumbnail_urls()
		ret['is_installed'] = app.is_installed()
		ret['is_current'] = app.without_repository or ucr_get('repository/online/component/%s' % app.component_id) == 'enabled'
		ret['local_role'] = ucr_get('server/role')
		ret['is_master'] = ret['local_role'] == 'domaincontroller_master'
		ret['host_master'] = ucr_get('ldap/master')
		ret['is_ucs_component'] = app.is_ucs_component()
		ret.update(cls._candidate_dict(app))
		return ret

	@classmethod
	def _candidate_dict(cls, app):
		ret = {}
		if app.is_installed():
			candidate = Apps().find_candidate(app)
		else:
			candidate = None
		if candidate:
			ret['update_available'] = True
			ret['candidate_docker'] = candidate.docker
			ret['candidate_version'] = candidate.version
			ret['candidate_component_id'] = candidate.component_id
			ret['candidate_readme_update'] = candidate.readme_update
			ret['candidate_readme_post_update'] = candidate.readme_post_update
			ret['candidate_needs_install_permissions'] = not candidate.install_permissions_exist()
			ret['candidate_install_permissions_message'] = candidate.install_permissions_message
		else:
			ret['update_available'] = False  # TODO: ucr.is_true(app.ucr_upgrade_key); Bug#39916
			ret['candidate_needs_install_permissions'] = not app.install_permissions_exist()
			ret['candidate_install_permissions_message'] = app.install_permissions_message
		return ret

	@classmethod
	def raw_value(cls, app, section, option):
		config_parser = CaseSensitiveConfigParser()
		with open(app.get_ini_file(), 'rb') as f:
			config_parser.readfp(f)
		try:
			return config_parser.get(section, option)
		except (NoSectionError, NoOptionError):
			return None

	def get_values(self, app, keys, warn=True):
		config_parser = CaseSensitiveConfigParser()
		with open(app.get_ini_file(), 'rb') as f:
			config_parser.readfp(f)
		for section, key in keys:
			search_section = section or 'Application'
			found = False
			for config_section in config_parser.sections():
				if _match(config_section, search_section):
					for name, value in config_parser.items(config_section):
						if _match(name, key):
							for attr in app._attrs:
								ini_attr_name = attr.name.replace('_', '')
								if ini_attr_name == name.lower():
									value = attr.get(value, app.get_ini_file())
							found = True
							result_section = section and config_section
							yield result_section, name, value
			if not found:
				try:
					value = getattr(app, key)
					if callable(value):
						raise AttributeError(key)
				except AttributeError:
					if warn:
						self.warn('Could not find option %s:%s' % (search_section, key))
				else:
					yield None, key, value
