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
import re

from ldap.dn import str2dn, dn2str

from univention.config_registry.frontend import ucr_update
from univention.config_registry import ConfigRegistry

from univention.appcenter.app import AppManager
from univention.appcenter.udm import create_object_if_not_exists, init_object, get_app_ldap_object, remove_object_if_exists
from univention.appcenter.actions import StoreAppAction
from univention.appcenter.actions.credentials import CredentialsAction
from univention.appcenter.utils import mkdir, rmdir, get_md5, app_ports
from univention.appcenter.log import catch_stdout


class NoMorePorts(Exception):
	pass


class Register(CredentialsAction):
	'''Registers one or more applications. Done automatically via install, only useful if something went wrong / finer grained control is needed.'''
	help = 'Registers an app'

	def setup_parser(self, parser):
		super(Register, self).setup_parser(parser)
		parser.add_argument('--files', dest='register_task', action='append_const', const='files', help='Creating shared directories; copying files from App Center server')
		parser.add_argument('--component', dest='register_task', action='append_const', const='component', help='Adding the component to the list of available repositories')
		parser.add_argument('--host', dest='register_task', action='append_const', const='host', help='Creating a computer object for the app (docker apps only)')
		parser.add_argument('--app', dest='register_task', action='append_const', const='app', help='Registering the app itself (internal UCR variables, ucs-overview variables, adding a special LDAP object for the app)')
		parser.add_argument('--do-it', dest='do_it', action='store_true', default=None, help='Always do it, disregarding installation status')
		parser.add_argument('--undo-it', dest='do_it', action='store_false', default=None, help='Undo any registrations, disregarding installation status')
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

	def _do_register(self, app, args):
		if args.do_it is None:
			return app.is_installed()
		return args.do_it

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
			if self._do_register(app, args):
				updates.update(self._register_component(app, ucr, server, delay=True))
			else:
				updates.update(self._unregister_component_dict(app, ucr))
		with catch_stdout(self.logger):
			ucr_update(ucr, updates)

	def _register_component(self, app, ucr=None, server=None, delay=False):
		if ucr is None:
			ucr = ConfigRegistry()
			ucr.load()
		if app.docker and not ucr.get('docker/container/uuid'):
			self.log('Component needs to be registered in the container')
			return {}
		if app.without_repository:
			self.log('No repository to register')
			return {}
		if server is None:
			server = AppManager.get_server()
			server = server[server.find('/') + 2:]
		updates = {}
		self.log('Registering component for %s' % app.id)
		for _app in AppManager.get_all_apps_with_id(app.id):
			if _app == app:
				updates.update(self._register_component_dict(_app, ucr, server))
			else:
				updates.update(self._unregister_component_dict(_app, ucr))
		if not delay:
			with catch_stdout(self.logger):
				ucr_update(ucr, updates)
		return updates

	def _ucr_component_base(self, app):
		return 'repository/online/component/%s' % app.component_id

	def _register_component_dict(self, app, ucr, server):
		ret = {}
		ucr_base_key = self._ucr_component_base(app)
		self.debug('Adding %s' % ucr_base_key)
		ret[ucr_base_key] = 'enabled'
		ucr_base_key = '%s/%%s' % ucr_base_key
		ret[ucr_base_key % 'server'] = server
		ret[ucr_base_key % 'description'] = app.name
		ret[ucr_base_key % 'localmirror'] = 'false'
		ret[ucr_base_key % 'version'] = ucr.get(ucr_base_key % 'version', 'current')
		return ret

	def _unregister_component_dict(self, app, ucr):
		ret = {}
		ucr_base_key = self._ucr_component_base(app)
		for key in ucr.keys():
			if key == ucr_base_key or key.startswith('%s/' % ucr_base_key):
				self.debug('Removing %s' % key)
				ret[key] = None
		return ret

	def _register_files_for_apps(self, apps, args):
		if not self._shall_register(args, 'files'):
			return
		for app in apps:
			if self._do_register(app, args):
				self._register_files(app)
			else:
				self._unregister_files(app)

	def _register_files(self, app):
		self.log('Creating data directories for %s...' % app.id)
		mkdir(app.get_data_dir())
		mkdir(app.get_conf_dir())
		mkdir(app.get_share_dir())
		for ext in ['univention-config-registry-variables', 'schema']:
			fname = app.get_cache_file(ext)
			if os.path.exists(fname):
				self.log('Copying %s' % fname)
				shutil.copy2(fname, app.get_share_file(ext))

	def _unregister_files(self, app):
		self.log('Removing data directories for %s...' % app.id)
		rmdir(app.get_data_dir())
		rmdir(app.get_conf_dir())
		rmdir(app.get_share_dir())

	def _register_host_for_apps(self, apps, args):
		if not self._shall_register(args, 'host'):
			return
		for app in apps:
			if self._do_register(app, args):
				self._register_host(app, args)
			else:
				self._unregister_host(app, args)

	def _register_host(self, app, args):
		if not app.docker:
			self.debug('App is not docker. Skip registering host')
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
		hostname = '%s-%d' % (app.id[:46], time.time() * 1000000)
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
		obj = create_object_if_not_exists('computers/%s' % app.docker_server_role, lo, pos, name=hostname, description=description, domain=domain, password=password, objectFlag='docker', policies=policies)
		ucr_update(ucr, {app.ucr_hostdn_key: obj.dn})
		return obj.dn, password

	def _unregister_host(self, app, args):
		ucr = ConfigRegistry()
		ucr.load()
		hostdn = ucr.get(app.ucr_hostdn_key)
		if not hostdn:
			self.log('No hostdn for %s found. Nothing to remove' % app.id)
			return
		lo, pos = self._get_ldap_connection(args)
		remove_object_if_exists('computers/%s' % app.docker_server_role, lo, pos, hostdn)
		ucr_update(ucr, {app.ucr_hostdn_key: None})

	def _register_app_for_apps(self, apps, args):
		if not self._shall_register(args, 'app'):
			return
		ucr = ConfigRegistry()
		ucr.load()
		updates = {}
		if apps:
			lo, pos = self._get_ldap_connection(args, allow_machine_connection=True)
		for app in apps:
			if self._do_register(app, args):
				updates.update(self._register_app(app, args, ucr, lo, pos, delay=True))
			else:
				updates.update(self._unregister_app(app, args, ucr, lo, pos, delay=True))
		ucr_update(ucr, updates)

	def _register_app(self, app, args, ucr=None, lo=None, pos=None, delay=False):
		if ucr is None:
			ucr = ConfigRegistry()
			ucr.load()
		if lo is None:
			lo, pos = self._get_ldap_connection(args, allow_machine_connection=True)
		updates = {}
		self.log('Registering UCR for %s' % app.id)
		self.log('Marking %s as installed' % app)
		if app.is_installed():
			status = ucr.get(app.ucr_status_key)
		else:
			status = 'installed'
		ucr_update(ucr, {app.ucr_status_key: status, app.ucr_version_key: app.version})
		updates.update(self._register_docker_variables(app, ucr))
		updates.update(self._register_app_report_variables(app, ucr))
		# Register app in LDAP (cn=...,cn=apps,cn=univention)
		ldap_object = get_app_ldap_object(app, lo, pos, ucr, or_create=True)
		self.log('Adding localhost to LDAP object')
		ldap_object.add_localhost()
		updates.update(self._register_overview_variables(app, ucr))
		if not delay:
			ucr_update(ucr, updates)
			self._reload_apache()
		return updates

	def _register_docker_variables(self, app, ucr):
		updates = {}
		if app.docker:
			try:
				from univention.appcenter.actions.service import Service, ORIGINAL_INIT_SCRIPT
			except ImportError:
				# univention-appcenter-docker is not installed
				pass
			else:
				try:
					init_script = Service.get_init(app)
					self.log('Creating %s' % init_script)
					os.symlink(ORIGINAL_INIT_SCRIPT, init_script)
					self._call_script('update-rc.d', os.path.basename(init_script), 'defaults', '41', '14')
				except OSError as exc:
					msg = str(exc)
					if exc.errno == 17:
						self.log(msg)
					else:
						self.warn(msg)
				updates[app.ucr_image_key] = app.get_docker_image_name()
				port_updates = {}
				current_port_config = {}
				for app_id, container_port, host_port in app_ports():
					if app_id == app.id:
						current_port_config[app.ucr_ports_key % container_port] = str(host_port)
						port_updates[app.ucr_ports_key % container_port] = None
				for port in app.ports_exclusive:
					port_updates[app.ucr_ports_key % port] = str(port)
				for port in app.ports_redirection:
					host_port, container_port = port.split(':')
					port_updates[app.ucr_ports_key % container_port] = str(host_port)
				if app.auto_mod_proxy and app.has_local_web_interface():
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
					if app.web_interface_port_http:
						key = app.ucr_ports_key % app.web_interface_port_http
						value = str(next_port)
						if key in current_port_config:
							value = current_port_config[key]
						port_updates[key] = value
						next_port = max(ports_taken) + 2
					if app.web_interface_port_https:
						key = app.ucr_ports_key % app.web_interface_port_https
						value = str(next_port)
						if key in current_port_config:
							value = current_port_config[key]
						port_updates[key] = value
				for container_port, host_port in current_port_config.iteritems():
					if container_port in port_updates:
						if port_updates[container_port] == host_port:
							port_updates.pop(container_port)
				if port_updates:
					ucr_update(ucr, port_updates)
					updates.update(port_updates)
		return updates

	def _register_app_report_variables(self, app, ucr):
		updates = {}
		for key in ucr.iterkeys():
			if re.match('appreport/%s/' % app.id, key):
				updates[key] = None
		registry_key = 'appreport/%s/%%s' % app.id
		anything_set = False
		for key in ['object_type', 'object_filter', 'object_attribute', 'attribute_type', 'attribute_filter']:
			value = getattr(app, 'app_report_%s' % key)
			if value:
				anything_set = True
			updates[registry_key % key] = value
		if anything_set:
			updates[registry_key % 'report'] = 'yes'
		return updates

	def _register_overview_variables(self, app, ucr):
		updates = {}
		for key in ucr.iterkeys():
			if re.match('ucs/web/overview/entries/[^/]+/%s/' % app.id, key):
				updates[key] = None
		if app.ucs_overview_category and app.web_interface:
			self.log('Setting overview variables')
			registry_key = 'ucs/web/overview/entries/%s/%s/%%s' % (app.ucs_overview_category, app.id)
			variables = {
				'icon': '/univention-management-console/js/dijit/themes/umc/icons/scalable/%s' % app.logo,
				'port_http': str(app.web_interface_port_http or ''),
				'port_https': str(app.web_interface_port_https or ''),
				'label': app.get_localised('name'),
				'label/de': app.get_localised('name', 'de'),
				'description': app.get_localised('description'),
				'description/de': app.get_localised('description', 'de'),
				'link': app.web_interface,
			}
			for key, value in variables.iteritems():
				updates[registry_key % key] = value
		return updates

	def _unregister_app(self, app, args, ucr=None, lo=None, pos=None, delay=False):
		if ucr is None:
			ucr = ConfigRegistry()
			ucr.load()
		if lo is None:
			lo, pos = self._get_ldap_connection(args, allow_machine_connection=True)
		updates = {}
		if app.is_installed():
			for key in ucr.iterkeys():
				if key.startswith('appcenter/apps/%s/' % app.id):
					updates[key] = None
				if re.match('ucs/web/overview/entries/[^/]+/%s/' % app.id, key):
					updates[key] = None
				if re.match('appreport/%s/' % app.id, key):
					updates[key] = None
			if app.docker:
				try:
					from univention.appcenter.actions.service import Service
				except ImportError:
					# univention-appcenter-docker is not installed
					pass
				else:
					try:
						init_script = Service.get_init(app)
						os.unlink(init_script)
						self._call_script('update-rc.d', os.path.basename(init_script), 'remove')
					except OSError:
						pass
			ldap_object = get_app_ldap_object(app, lo, pos, ucr)
			if ldap_object:
				self.log('Removing localhost from LDAP object')
				ldap_object.remove_localhost()
			if not delay:
				ucr_update(ucr, updates)
				self._reload_apache()
		else:
			self.log('%s is not installed. Cannot unregister' % app)
		return updates
