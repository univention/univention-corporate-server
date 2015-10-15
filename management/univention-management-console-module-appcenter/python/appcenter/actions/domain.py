#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for managing apps in the domain
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

from univention.config_registry import ConfigRegistry

from univention.appcenter.log import LogCatcher
from univention.appcenter.utils import call_process
from univention.appcenter.udm import search_objects
from univention.appcenter.app import AppManager
from univention.appcenter.actions.credentials import CredentialsAction
from univention.appcenter.actions import get_action


class Domain(CredentialsAction):
	'''Shows information about the domain and enabled management of app installations.'''
	help = 'Domain management'

	def setup_parser(self, parser):
		pass

	def main(self, args):
		lo, pos = self._get_ldap_connection(args, allow_machine_connection=True)
		first = True
		ucr = ConfigRegistry()
		ucr.load()
		localhost = ucr.get('hostname')
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
				if 'docker' not in obj.info.get('objectFlag', []):
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
		get = get_action('get')
		ucr = ConfigRegistry()
		ucr.load()
		ret = []
		for app in apps:
			if not app:
				ret.append(None)
			else:
				app_dict = get.to_dict(app)
				app_dict['installations'] = self.get_installations(app, hosts, lo, pos, ucr)
				ret.append(app_dict)
		return ret

	def get_installations(self, app, hosts, lo, pos, ucr):
		ret = {}
		container = 'cn=%s,cn=apps,cn=univention,%s' % (app.id, ucr.get('ldap/base'))
		app_objects = search_objects('appcenter/app', lo, pos, container)
		for host in hosts:
			role = host.info.get('serverRole')[0]
			description = host.info.get('description')
			ip = host.info.get('ip')  # list
			version = None
			candidate_version = AppManager.find(app.id, latest=True).version
			for app_obj in app_objects:
				if host.info.get('fqdn') in app_obj.info.get('server', []):
					version = app_obj.info.get('version')
					break
			ret[host['name']] = {
				'version': version,
				'candidate_version': candidate_version,
				'description': description,
				'ip': ip,
				'role': role,
			}
		return ret
