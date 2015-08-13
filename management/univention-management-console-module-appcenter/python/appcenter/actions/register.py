#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app base module for registering an app
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

import os.path
import shutil
import time

from ldap.dn import str2dn, dn2str

from univention.config_registry.frontend import ucr_update
from univention.config_registry import ConfigRegistry

from univention.appcenter.app import AppManager
from univention.appcenter.udm import create_object_if_not_exists, init_object, get_app_ldap_object
from univention.appcenter.actions import StoreAppAction
from univention.appcenter.actions.credentials import CredentialsAction
from univention.appcenter.utils import mkdir, get_md5, app_ports

class NoMorePorts(Exception):
	pass

class Register(CredentialsAction):
	'''Registers one or more applications. Done automatically via install, only useful if something went wrong / finer grained control is needed.'''
	help='Registers an app'

	def setup_parser(self, parser):
		super(Register, self).setup_parser(parser)
		parser.add_argument('--files', dest='register_task', action='append_const', const='files')
		parser.add_argument('--component', dest='register_task', action='append_const', const='component')
		parser.add_argument('--host', dest='register_task', action='append_const', const='host')
		parser.add_argument('--app', dest='register_task', action='append_const', const='app')
		parser.add_argument('apps', nargs='*', action=StoreAppAction, help='The ID of the app that shall be registered')

	def main(self, args):
		apps = args.apps
		if not apps:
			self.debug('No apps given. Using all')
			apps = AppManager.get_all_apps()
		self._register_component_for_apps(apps, args)
		self._register_files_for_apps(apps, args)
		self._register_host_for_apps(apps, args)
		self._register_app_for_apps(apps, args)

	def _shall_register(self, args, task):
		return args.register_task is None or task in args.register_task

	def _register_component_for_apps(self, apps, args):
		if not self._shall_register(args, 'component'):
			return
		server = AppManager.get_server()
		server = server[server.find('/') + 2:]
		ucr = ConfigRegistry()
		ucr.load()
		updates = {}
		for app in apps:
			updates.update(self._register_component(app, ucr, server, delay=True, force=self._explicit(args)))
		ucr_update(ucr, updates)

	def _register_component(self, app, ucr=None, server=None, delay=False, force=True):
		if app.docker and not force:
			return {}
		if ucr is None:
			ucr = ConfigRegistry()
			ucr.load()
		if server is None:
			server = AppManager.get_server()
			server = server[server.find('/') + 2:]
		updates = {}
		self.log('Registering component for %s' % app.id)
		for _app in AppManager.get_all_apps_with_id(app.id):
			updates.update(self._register_component_dict(_app, server, ucr, force=False))
		if force:
			updates.update(self._register_component_dict(app, server, ucr, force=True))
		if not delay:
			ucr_update(ucr, updates)
		return updates

	def _ucr_component_base(self, app):
		return 'repository/online/component/%s' % app.component_id

	def _register_component_dict(self, app, server, ucr, force):
		ret = {}
		ucr_base_key = self._ucr_component_base(app)
		to_be_added = force or app.is_installed() and (not app.docker or ucr.get(app.ucr_container_key))
		if to_be_added:
			ucr_base_key = self._ucr_component_base(app)
			self.debug('Adding %s' % ucr_base_key)
			ret[ucr_base_key] = 'enabled'
			ucr_base_key = '%s/%%s' % ucr_base_key
			ret[ucr_base_key % 'server'] = server
			ret[ucr_base_key % 'description'] = app.name
			ret[ucr_base_key % 'localmirror'] = 'false'
			ret[ucr_base_key % 'version'] = ucr.get(ucr_base_key % 'version', 'current')
		else:
			for key in ucr.keys():
				if key == ucr_base_key or key.startswith('%s/' % ucr_base_key):
					self.debug('Removing %s' % key)
					ret[key] = None
		return ret

	def _register_files_for_apps(self, apps, args):
		if not self._shall_register(args, 'files'):
			return
		for app in apps:
			self._register_files(app, force=self._explicit(args))

	def _explicit(self, args):
		return bool(args.apps) and args.register_task is not None

	def _register_files(self, app, force=True):
		if not app.docker:
			return
		if not force or not app.is_installed():
			return
		self.log('Creating data directories for %s...' % app.id)
		mkdir(app.get_data_dir())
		mkdir(app.get_conf_dir())
		mkdir(app.get_share_dir())
		for ext in ['univention-config-registry-variables', 'schema']:
			fname = app.get_cache_file(ext)
			if os.path.exists(fname):
				self.log('Copying %s' % fname)
				shutil.copy2(fname, app.get_share_file(ext))

	def _register_host_for_apps(self, apps, args):
		if not self._shall_register(args, 'host'):
			return
		for app in apps:
			self._register_host(app, args, force=self._explicit(args))

	def _register_host(self, app, args, force=True):
		if not app.docker:
			self.debug('App is not docker. Skip registering host')
			return None, None
		if not force and not app.is_installed():
			self.debug('App is not installed. Skip registering host')
			return None, None
		ucr = ConfigRegistry()
		ucr.load()
		hostdn = ucr.get(app.ucr_hostdn_key)
		lo, pos = self._get_ldap_connection(args)
		if hostdn:
			if lo.get(hostdn):
				self.log('Already found %s as a host for %s. Better do nothing...' % (hostdn, app.id))
				obj = init_object('computers/%s' % app.docker_server_role, lo, pos, hostdn)
				save = False
				for auto_update in ['packages', 'release']:
					policy_dn = 'cn=appcenter-update-%s,cn=policies,%s' % (auto_update, ucr.get('ldap/base'))
					if app.docker_auto_update == auto_update and policy_dn not in obj.policies:
						obj.policies.append(policy_dn)
						save = True
					elif app.docker_auto_update != auto_update and policy_dn in obj.policies:
						obj.policies.remove(policy_dn)
						save = True
				if save:
					self.log('... except changing release policy!')
					obj.save()
				return hostdn, None
			else:
				self.warn('%s should be the host for %s. But it was not found in LDAP. Creating a new one' % (hostdn, app.id))
		# quasi unique hostname; make sure it does not exceed 63 chars
		hostname = '%s-%d' % (app.component_id[:46], time.time() * 1000000)
		password = get_md5(time.time())
		self.log('Registering the container host %s for %s' % (hostname, app.id))
		if app.docker_server_role == 'memberserver':
			base = 'cn=memberserver,cn=computers,%s' % ucr.get('ldap/base')
		else:
			base = 'cn=dc,cn=computers,%s' % ucr.get('ldap/base')
		while base and not lo.get(base):
			base = dn2str(str2dn(base)[1:])
		pos.setDn(base)
		domain = ucr.get('domainname')
		description = '%s (%s)' % (app.name, app.version)
		policies = []
		if app.docker_auto_update == 'packages':
			policies = ['cn=appcenter-update-packages,cn=policies,%s' % ucr.get('ldap/base')]
		elif app.docker_auto_update == 'release':
			policies = ['cn=appcenter-update-release,cn=policies,%s' % ucr.get('ldap/base')]
		obj = create_object_if_not_exists('computers/%s' % app.docker_server_role, lo, pos, name=hostname, description=description, domain=domain, password=password, policies=policies)
		ucr_update(ucr, {app.ucr_hostdn_key: obj.dn})
		return obj.dn, password

	def _register_app_for_apps(self, apps, args):
		if not self._shall_register(args, 'app'):
			return
		ucr = ConfigRegistry()
		ucr.load()
		updates = {}
		for app in apps:
			updates.update(self._register_app(app, args, ucr, delay=True, force=self._explicit(args)))
		ucr_update(ucr, updates)

	def _register_app(self, app, args, ucr=None, delay=False, force=True):
		if ucr is None:
			ucr = ConfigRegistry()
			ucr.load()
		updates = {}
		priority_updates = {} # merged with updates, but overwrites it
		self.log('Registering UCR for %s' % app.id)
		lo, pos = self._get_ldap_connection(args, allow_machine_connection=True)
		for _app in AppManager.get_all_apps_with_id(app.id):
			if force and _app == app:
				self.log('Marking %s as installed' % _app)
				ucr_update(ucr, {_app.ucr_status_key: 'installed', _app.ucr_version_key: _app.version})
			is_installed = _app.is_installed()
			if is_installed and _app.docker:
				try:
					from univention.appcenter.actions.service import Start, ORIGINAL_INIT_SCRIPT
				except ImportError:
					# univention-appcenter-docker is not installed
					pass
				else:
					try:
						init_script = Start.get_init(_app)
						self.log('Creating %s' % init_script)
						os.symlink(ORIGINAL_INIT_SCRIPT, init_script)
					except OSError:
						pass
					for port in _app.ports_exclusive:
						updates[_app.ucr_ports_key % port] = str(port)
					for port in _app.ports_redirection:
						host_port, container_port = port.split(':')
						updates[_app.ucr_ports_key % container_port] = str(host_port)
					if _app.auto_mod_proxy and _app.has_local_web_interface():
						self.log('Setting ports for apache proxy')
						try:
							min_port = int(ucr.get('appcenter/ports/min'))
						except (TypeError, ValueError):
							min_port = 40000
						try:
							max_port = int(ucr.get('appcenter/ports/max'))
						except (TypeError, ValueError):
							max_port = 41000
						ports_taken = [min_port]
						for app_id, container_port, host_port in app_ports():
							if host_port < max_port:
								ports_taken.append(host_port)
						next_port = max(ports_taken) + 1
						if next_port > (max_port - 2):
							raise NoMorePorts(next_port)
						if _app.web_interface_port_http:
							updates[_app.ucr_ports_key % _app.web_interface_port_http] = str(next_port)
							next_port = max(ports_taken) + 2
						if _app.web_interface_port_https:
							updates[_app.ucr_ports_key % _app.web_interface_port_https] = str(next_port)

			# Register app in LDAP (cn=...,cn=apps,cn=univention)
			ldap_object = get_app_ldap_object(_app, lo, pos, ucr, or_create=is_installed)
			if is_installed:
				self.log('Adding localhost to LDAP object')
				ldap_object.add_localhost()
			else:
				if ldap_object:
					self.log('Removing localhost from LDAP object')
					ldap_object.remove_localhost()
					if not ldap_object.anywhere_installed():
						self.log('Removing LDAP object')
						ldap_object.remove_from_directory()

			if _app.ucs_overview_category and _app.web_interface:
				self.log('Setting overview variables')
				registry_key = 'ucs/web/overview/entries/%s/%s/%%s' % (_app.ucs_overview_category, _app.id)
				variables = {
					'icon' : '/univention-management-console/js/dijit/themes/umc/icons/50x50/%s' % _app.icon,
					'port_http' : str(_app.web_interface_port_http or ''),
					'port_https' : str(_app.web_interface_port_https or ''),
					'label' : _app.get_localised('name'),
					'label/de' : _app.get_localised('name', 'de'),
					'description' : _app.get_localised('description'),
					'description/de' : _app.get_localised('description', 'de'),
					'link' : _app.web_interface,
				}
				for key, value in variables.iteritems():
					if not is_installed:
						updates[registry_key % key] = None
					else:
						priority_updates[registry_key % key] = value
		updates.update(priority_updates)
		if not delay:
			ucr_update(ucr, updates)
			self._reload_apache()
		return updates

