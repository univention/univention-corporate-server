#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for managing apps in the domain
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

import re

from univention.appcenter.log import LogCatcher
from univention.appcenter.utils import call_process, get_local_fqdn
from univention.appcenter.udm import search_objects
from univention.appcenter.app_cache import Apps
from univention.appcenter.actions.credentials import CredentialsAction
from univention.appcenter.actions import get_action
from univention.appcenter.ucr import ucr_get, ucr_is_false


class Domain(CredentialsAction):

	'''Shows information about the domain and enabled management of app installations.'''
	help = 'Domain management'

	def setup_parser(self, parser):
		pass

	def main(self, args):
		lo, pos = self._get_ldap_connection(args, allow_machine_connection=True)
		first = True
		localhost = ucr_get('hostname')
		username = '%s$@%%s' % localhost
		pwdfile = '/etc/machine.secret'
		for obj in self.get_appcenter_hosts(lo, pos):
			if not first:
				self.log('')
			fqdn = obj.info.get('fqdn')
			self.log('%s:' % fqdn)
			logger = LogCatcher()
			output = self.manage(username % fqdn, pwdfile, logger, 'info')
			if output.has_stdout():
				for line in output.stdout():
					self.log(line)
			else:
				self.warn('Failed to get info')
				if output.has_stderr():
					for line in output.stderr():
						self.warn(line)
			first = False

	def get_appcenter_hosts(self, lo, pos):
		ret = []
		for role in ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver']:
			objs = search_objects('computers/%s' % role, lo, pos)
			for obj in objs:
				if not 'serverRole' in obj.info:
					continue
				if 'docker' in obj.info.get('objectFlag', []):
					continue
				ret.append(obj)
		return ret

	def manage(self, login, pwdfile, logger, *args):
		process_args = ['/usr/sbin/univention-ssh', pwdfile, login, 'univention-app'] + list(args)
		call_process(process_args, logger=logger)
		return logger

	@classmethod
	def to_dict(cls, apps):
		self = cls()
		lo, pos = self._get_ldap_connection(args=None, allow_machine_connection=True)
		hosts = self.get_appcenter_hosts(lo, pos)
		if ucr_is_false('appcenter/domainwide'):
			hostname = ucr_get('hostname')
			hosts = [host for host in hosts if host['name'] == hostname]
		get = get_action('get')
		ret = []
		app_ldap_objects = search_objects('appcenter/app', lo, pos)
		for app in apps:
			if not app:
				ret.append(None)
			else:
				app_dict = get.to_dict(app)
				app_dict['installations'] = self._get_installations(app, hosts, app_ldap_objects)
				app_dict['is_installed_anywhere'] = any(inst['version'] for inst in app_dict['installations'].itervalues())
				app_dict['fully_loaded'] = True
				ret.append(app_dict)
		return ret

	def _get_installations(self, app, hosts, app_ldap_objects):
		ret = {}
		local_ucs_version = ucr_get('version/version')
		for host in hosts:
			candidate = self._find_latest_app_version(app)
			role = host.info.get('serverRole')[0]
			description = host.info.get('description')
			remote_ucs_version = host.info.get('operatingSystemVersion')
			is_local = host.info.get('fqdn') == get_local_fqdn()
			if remote_ucs_version:
				remote_ucs_version = re.sub('.*([0-9]+\.[0-9]+).*', '\\1', remote_ucs_version)
			ip = host.info.get('ip')  # list
			version = None
			update_available = None
			for app_obj in app_ldap_objects:
				app_obj_version = app_obj.info.get('version')
				app_obj_id = app_obj.info.get('id')[:-len(app_obj_version) - 1]
				if app_obj_id == app.id:
					if host.info.get('fqdn') in app_obj.info.get('server', []):
						version = app_obj_version
						break
			if local_ucs_version != remote_ucs_version:
				# unable to compute directly... better treat as not available
				update_available = False
			elif version:
				remote_app = Apps().find(app.id, app_version=version)
				if remote_app:
					prevent_docker = None
					if not is_local:
						prevent_docker = True
					candidate = Apps().find_candidate(remote_app, prevent_docker=prevent_docker) or remote_app
					update_available = remote_app < candidate
			ret[host['name']] = {
				'ucs_version': remote_ucs_version,
				'version': version,
				'update_available': update_available,
				'candidate_version': candidate.version,
				'description': description,
				'ip': ip,
				'role': role,
			}
		return ret

	def _find_latest_app_version(self, app):
		candidate = Apps().find_candidate(app)
		return candidate or app
