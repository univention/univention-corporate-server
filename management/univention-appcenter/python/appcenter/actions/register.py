#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app base module for registering an app
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

import os.path
import shutil
import time
import re
from optparse import Values

from ldap.dn import str2dn, dn2str
from distutils.version import LooseVersion

from univention.lib.ldap_extension import UniventionLDAPSchema

from univention.appcenter.app_cache import Apps
from univention.appcenter.packages import reload_package_manager
from univention.appcenter.udm import create_object_if_not_exists, get_app_ldap_object, remove_object_if_exists, create_recursive_container
from univention.appcenter.database import DatabaseConnector, DatabaseError
from univention.appcenter.extended_attributes import get_schema, get_extended_attributes, create_extended_attribute, remove_extended_attribute, create_extended_option, remove_extended_option
from univention.appcenter.actions import StoreAppAction, get_action
from univention.appcenter.exceptions import DatabaseConnectorError, RegisterSchemaFailed, RegisterSchemaFileFailed
from univention.appcenter.actions.credentials import CredentialsAction
from univention.appcenter.utils import mkdir, app_ports, app_ports_with_protocol, currently_free_port_in_range, generate_password, container_mode
from univention.appcenter.log import catch_stdout, LogCatcher
from univention.appcenter.ucr import ucr_save, ucr_get, ucr_keys, ucr_instance


class Register(CredentialsAction):

	'''Registers one or more applications. Done automatically via install, only useful if something went wrong / finer grained control is needed.'''
	help = 'Registers an app'

	def setup_parser(self, parser):
		super(Register, self).setup_parser(parser)
		parser.add_argument('--component', dest='register_task', action='append_const', const='component', help='Adding the component to the list of available repositories')
		parser.add_argument('--files', dest='register_task', action='append_const', const='files', help='Creating shared directories; copying files from App Center server')
		parser.add_argument('--host', dest='register_task', action='append_const', const='host', help='Creating a computer object for the app (docker apps only)')
		parser.add_argument('--app', dest='register_task', action='append_const', const='app', help='Registering the app itself (internal UCR variables, ucs-overview variables, adding a special LDAP object for the app)')
		parser.add_argument('--database', dest='register_task', action='append_const', const='database', help='Installing, starting a database management system and creating a database for the app (if necessary)')
		parser.add_argument('--attributes', dest='register_task', action='append_const', const='attributes', help='Adding schema extions to LDAP; adding extended attributes')
		parser.add_argument('--listener', dest='register_task', action='append_const', const='listener', help='Adding listener for App')
		parser.add_argument('--do-it', dest='do_it', action='store_true', default=None, help='Always do it, disregarding installation status')
		parser.add_argument('--undo-it', dest='do_it', action='store_false', default=None, help='Undo any registrations, disregarding installation status')
		parser.add_argument('apps', nargs='*', action=StoreAppAction, help='The ID of the App that shall be registered')

	def main(self, args):
		reload_package_manager()
		apps = args.apps
		if not apps:
			self.debug('No apps given. Using all')
			apps = Apps().get_all_apps()
		self._register_component_for_apps(apps, args)
		self._register_files_for_apps(apps, args)
		self._register_host_for_apps(apps, args)
		self._register_app_for_apps(apps, args)
		self._register_database_for_apps(apps, args)
		self._register_attributes_for_apps(apps, args)
		self._register_listener_for_apps(apps, args)
		self._register_installed_apps_in_ucr()

	def _do_register(self, app, args):
		if args.do_it is None:
			return app.is_installed()
		return args.do_it

	def _shall_register(self, args, task):
		return args.register_task is None or task in args.register_task

	def _register_component_for_apps(self, apps, args):
		if not self._shall_register(args, 'component'):
			return
		updates = {}
		for app in apps:
			if self._do_register(app, args):
				updates.update(self._register_component(app, delay=True))
			else:
				updates.update(self._unregister_component_dict(app))
		with catch_stdout(self.logger):
			ucr_save(updates)

	def _register_component(self, app, delay=False):
		if app.docker and not container_mode():
			self.log('Component needs to be registered in the container')
			return {}
		if app.without_repository:
			self.log('No repository to register')
			return {}
		updates = {}
		self.log('Registering component for %s' % app)
		for _app in Apps().get_all_apps_with_id(app.id):
			if _app == app:
				updates.update(self._register_component_dict(_app))
			else:
				updates.update(self._unregister_component_dict(_app))
		if not delay:
			with catch_stdout(self.logger):
				if not ucr_save(updates):
					updates = {}
		return updates

	def _register_component_dict(self, app):
		ret = {}
		ucr_base_key = app.ucr_component_key
		self.debug('Adding %s' % ucr_base_key)
		ret[ucr_base_key] = 'enabled'
		ucr_base_key = '%s/%%s' % ucr_base_key
		ret[ucr_base_key % 'server'] = app.get_server()
		ret[ucr_base_key % 'description'] = app.name
		ret[ucr_base_key % 'localmirror'] = 'false'
		ret[ucr_base_key % 'version'] = ucr_get(ucr_base_key % 'version', 'current')
		return ret

	def _unregister_component(self, app):
		if app.without_repository:
			self.log('No repository to unregister')
			return {}
		updates = self._unregister_component_dict(app)
		if not ucr_save(updates):
			updates = {}
		return updates

	def _unregister_component_dict(self, app):
		ret = {}
		ucr_base_key = app.ucr_component_key
		for key in ucr_keys():
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
			else:
				if ext == 'schema':
					schema = get_schema(app)
					if schema:
						with open(app.get_share_file(ext), 'wb') as fd:
							fd.write(schema)

	def _unregister_files(self, app):
		# not removing anything here. these may be important backup files
		pass

	def _register_attributes_for_apps(self, apps, args):
		if not self._shall_register(args, 'attributes'):
			return
		lo, pos = self._get_ldap_connection(args)
		for app in apps:
			ldap_object = get_app_ldap_object(app, lo, pos)
			if self._do_register(app, args):
				domain = get_action('domain')
				i = domain.to_dict([app])[0]['installations']
				if all(LooseVersion(ucr_get('version/version')) >= LooseVersion(x['ucs_version']) for x in i.values() if x['ucs_version']):
					self._register_attributes(app, args)
				else:
					self.debug('Not registering attributes. App is not the latest version in domain.')
			elif ldap_object.get_siblings():
				self.debug('Not removing attributes, App is still installed somewhere')
			else:
				self._unregister_attributes(app, args)

	def _register_attributes(self, app, args):
		# FIXME: there is no better lib function than this snippet
		schema_file = app.get_share_file('schema')
		if os.path.exists(schema_file):
			self.log('Registering schema %s' % schema_file)
			lo, pos = self._get_ldap_connection(args)
			with self._get_password_file(args) as password_file:
				create_recursive_container('cn=ldapschema,cn=univention,%s' % ucr_get('ldap/base'), lo, pos)
				if app.automatic_schema_creation:
					schema_obj = UniventionLDAPSchema(ucr_instance())
					userdn = self._get_userdn(args)
					udm_passthrough_options = ['--binddn', userdn, '--bindpwdfile', password_file]
					opts = Values()
					opts.packagename = 'appcenter-app-%s' % app.id
					opts.packageversion = app.version
					opts.ucsversionstart = None
					opts.ucsversionend = None
					os.environ['UNIVENTION_APP_IDENTIFIER'] = app.id
					try:
						schema_obj.register(schema_file, opts, udm_passthrough_options)
					except SystemExit as exc:
						if exc.code == 4:
							self.warn('A newer version of %s has already been registered. Skipping...' % schema_file)
						else:
							raise RegisterSchemaFailed(exc.code)
					else:
						if not schema_obj.wait_for_activation():
							raise RegisterSchemaFileFailed(schema_file)
					finally:
						if 'UNIVENTION_APP_IDENTIFIER' in os.environ:
							del os.environ['UNIVENTION_APP_IDENTIFIER']

				# and this is what should be there after one line of lib.register_schema(schema_file)
				app = app.get_app_cache_obj().copy(locale='en').find_by_component_id(app.component_id)
				attributes, __, options = get_extended_attributes(app)
				for option in options:
					self.log('Registering option %s' % option.name)
					create_extended_option(option, app, lo, pos)
				if attributes:
					for i, attribute in enumerate(attributes):
						self.log('Registering attribute %s' % attribute.name)
						create_extended_attribute(attribute, app, i + 1, lo, pos)

	def _unregister_attributes(self, app, args):
		attributes, __, options = get_extended_attributes(app)
		if attributes or options:
			lo, pos = self._get_ldap_connection(args)
			for attribute in attributes:
				remove_extended_attribute(attribute, lo, pos)
			for option in options:
				remove_extended_option(option, lo, pos)

	def _register_listener_for_apps(self, apps, args):
		if not self._shall_register(args, 'listener'):
			return
		restart = False
		meta_files = []
		for app in apps:
			if self._do_register(app, args):
				restart = self._register_listener(app, delay=True) or restart
			else:
				meta_file = self._unregister_listener(app, delay=True)
				if meta_file:
					restart = True
					meta_files.append(meta_file)
		if restart:
			self._restart_listener(meta_files)

	def _register_listener(self, app, delay=False):
		if app.listener_udm_modules:
			listener_file = '/usr/lib/univention-directory-listener/system/%s.py' % app.id
			if os.path.exists(listener_file):
				return
			ldap_filter = '(|%s)' % ''.join('(univentionObjectType=%s)' % udm_module for udm_module in app.listener_udm_modules)
			dump_dir = os.path.join('/var/lib/univention-appcenter/listener/', app.id)  # this is appcenter.listener.LISTENER_DUMP_DIR, but save the import for just that
			output_dir = os.path.join(app.get_data_dir(), 'listener')
			with open(listener_file, 'w') as fd:
				fd.write('''#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
__package__ = ''  # workaround for PEP 366


from univention.appcenter.listener import AppListener

name = '%(name)s'

class AppListener(AppListener):
	class Configuration(AppListener.Configuration):
		name = '%(name)s'
		# the following attributes do nothing and are here solely for
		# documentation / transparency purposes
		# logic is in the AppListener class itself
		ldap_filter = '%(ldap_filter)s'
		dump_dir = '%(dump_dir)s'
		output_dir = '%(output_dir)s'
''' % {'name': app.id, 'ldap_filter': ldap_filter, 'dump_dir': dump_dir, 'output_dir': output_dir})
			self._update_converter_service(app)
			self.log('Added Listener for %s' % app)
			if not delay:
				self._restart_listener([])
			return True
		else:
			pass  # do not remove any listener. could be installed properly by packages

	def _update_converter_service(self, app):
		listener_file = '/usr/lib/univention-directory-listener/system/%s.py' % app.id
		if os.path.exists(listener_file):
			logger = LogCatcher()
			self._subprocess(['systemctl', 'is-enabled', 'univention-appcenter-listener-converter@%s.service' % app.id], logger)
			if list(logger.stdout()) == ['enabled']:
				self._subprocess(['systemctl', 'restart', 'univention-appcenter-listener-converter@%s.service' % app.id])
			else:
				self._subprocess(['systemctl', 'enable', 'univention-appcenter-listener-converter@%s.service' % app.id])
				self._subprocess(['systemctl', 'start', 'univention-appcenter-listener-converter@%s.service' % app.id])
		else:
			self._subprocess(['systemctl', 'stop', 'univention-appcenter-listener-converter@%s.service' % app.id])
			self._subprocess(['systemctl', 'disable', 'univention-appcenter-listener-converter@%s.service' % app.id])

	def _unregister_listener(self, app, delay=False):
		if app.listener_udm_modules:
			listener_file = '/usr/lib/univention-directory-listener/system/%s.py' % app.id
			listener_meta_file = '/var/lib/univention-directory-listener/handlers/%s' % app.id
			if os.path.exists(listener_file):
				os.unlink(listener_file)
				self._update_converter_service(app)
				self.log('Removed Listener for %s' % app)
				if not delay:
					self._restart_listener([listener_meta_file])
				return listener_meta_file

	def _restart_listener(self, meta_files):
		self.log('Restarting Listener...')
		self._subprocess(['service', 'univention-directory-listener', 'crestart'])
		for meta_file in meta_files:
			if os.path.exists(meta_file):
				self.debug('Removed leftover file %s. Useful for re-installations' % meta_file)
				os.unlink(meta_file)

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
		hostdn = ucr_get(app.ucr_hostdn_key)
		lo, pos = self._get_ldap_connection(args)
		if hostdn:
			if lo.get(hostdn):
				self.log('Already found %s as a host for %s. Trying to retrieve machine secret.' % (hostdn, app.id))
				password = None
				if os.path.isfile(app.secret_on_host):
					with open(app.secret_on_host) as pwfile:
						password = pwfile.read()
				return hostdn, password
			else:
				self.warn('%s should be the host for %s. But it was not found in LDAP. Creating a new one' % (hostdn, app.id))
		# quasi unique hostname; make sure it does not exceed 14 chars
		# 5 chars of appid + '-' + 8 digits of Epoch
		hostname = '%s-%s' % (app.id[:5], str(int((time.time() * 1000000)))[-10:-2])
		password = generate_password()
		self.log('Registering the container host %s for %s' % (hostname, app.id))
		if app.docker_server_role == 'memberserver':
			base = 'cn=memberserver,cn=computers,%s' % ucr_get('ldap/base')
		else:
			base = 'cn=dc,cn=computers,%s' % ucr_get('ldap/base')
		while base and not lo.get(base):
			base = dn2str(str2dn(base)[1:])
		pos.setDn(base)
		domain = ucr_get('domainname')
		description = '%s (%s)' % (app.name, app.version)
		policies = ['cn=app-release-update,cn=policies,%s' % ucr_get('ldap/base'), 'cn=app-update-schedule,cn=policies,%s' % ucr_get('ldap/base')]
		obj = create_object_if_not_exists('computers/%s' % app.docker_server_role, lo, pos, name=hostname, description=description, domain=domain, password=password, objectFlag='docker', policies=policies)
		ucr_save({app.ucr_hostdn_key: obj.dn})
		# save password on docker host
		if password:
			with open(app.secret_on_host, 'w+b') as f:
				os.chmod(app.secret_on_host, 0o600)
				f.write(password)
		return obj.dn, password

	def _unregister_host(self, app, args):
		hostdn = ucr_get(app.ucr_hostdn_key)
		if not hostdn:
			self.log('No hostdn for %s found. Nothing to remove' % app.id)
			return
		lo, pos = self._get_ldap_connection(args)
		remove_object_if_exists('computers/%s' % app.docker_server_role, lo, pos, hostdn)
		ucr_save({app.ucr_hostdn_key: None})

	def _register_app_for_apps(self, apps, args):
		if not self._shall_register(args, 'app'):
			return
		updates = {}
		if apps:
			lo, pos = self._get_ldap_connection(args, allow_machine_connection=True)
		for app in apps:
			if self._do_register(app, args):
				updates.update(self._register_app(app, args, lo, pos, delay=True))
			else:
				updates.update(self._unregister_app(app, args, lo, pos, delay=True))
		ucr_save(updates)

	def _register_app(self, app, args, lo=None, pos=None, delay=False):
		if lo is None:
			lo, pos = self._get_ldap_connection(args, allow_machine_connection=True)
		updates = {}
		self.log('Registering UCR for %s' % app.id)
		self.log('Marking %s as installed' % app)
		if app.is_installed():
			status = ucr_get(app.ucr_status_key, 'installed')
		else:
			status = 'installed'
		ucr_save({app.ucr_status_key: status, app.ucr_version_key: app.version, app.ucr_ucs_version_key: app.get_ucs_version()})
		self._register_ports(app)
		updates.update(self._register_docker_variables(app))
		updates.update(self._register_app_report_variables(app))
		# Register app in LDAP (cn=...,cn=apps,cn=univention)
		ldap_object = get_app_ldap_object(app, lo, pos, or_create=True)
		self.log('Adding localhost to LDAP object')
		ldap_object.add_localhost()
		updates.update(self._register_overview_variables(app))
		if not delay:
			ucr_save(updates)
			self._reload_apache()
		return updates

	def _register_database_for_apps(self, apps, args):
		if not self._shall_register(args, 'database'):
			return
		for app in apps:
			if self._do_register(app, args):
				self._register_database(app)

	def _register_database(self, app):
		database_connector = DatabaseConnector.get_connector(app)
		if database_connector:
			try:
				database_connector.create_database()
			except DatabaseError as exc:
				raise DatabaseConnectorError(exc.exception_value())

	def _register_docker_variables(self, app):
		updates = {}
		if app.docker and not app.plugin_of:
			try:
				from univention.appcenter.actions.service import Service, ORIGINAL_INIT_SCRIPT
			except ImportError:
				# univention-appcenter-docker is not installed
				pass
			else:
				if not app.uses_docker_compose():
					try:
						init_script = Service.get_init(app)
						self.log('Creating %s' % init_script)
						with open(ORIGINAL_INIT_SCRIPT, 'r') as source:
							lines = source.readlines()
						with open(init_script, 'w') as target:
							for line in lines:
								target.write(re.sub(r'@%@APPID@%@', app.id, line))
						os.chmod(init_script, 0o755)
						self._call_script('/usr/sbin/update-rc.d', os.path.basename(init_script), 'defaults', '41', '14')
						self._call_script('/bin/systemctl', 'daemon-reload')
					except OSError as exc:
						msg = str(exc)
						if exc.errno == 17:
							self.log(msg)
						else:
							self.warn(msg)
				updates[app.ucr_image_key] = app.get_docker_image_name()
		return updates

	def _register_ports(self, app):
		updates = {}
		current_port_config = {}
		for app_id, container_port, host_port in app_ports():
			if app_id == app.id:
				current_port_config[app.ucr_ports_key % container_port] = str(host_port)
				updates[app.ucr_ports_key % container_port] = None
				updates[app.ucr_ports_key % container_port + '/protocol'] = None
		if app.docker and app.plugin_of:
			# handling for plugins of Docker Apps: copy ports of base App
			for app_id, container_port, host_port, proto in app_ports_with_protocol():
				if app_id == app.plugin_of:
					updates[app.ucr_ports_key % container_port] = str(host_port)
					updates[app.ucr_ports_key % container_port + '/protocol'] = proto
			ucr_save(updates)
			return
		for port in app.ports_exclusive:
			updates[app.ucr_ports_key % port] = str(port)
		redirection_ports = []
		for port in app.ports_redirection:
			redirection_ports.append((port, 'tcp'))
		for port in app.ports_redirection_udp:
			redirection_ports.append((port, 'udp'))
		for port, protocol in redirection_ports:
			host_port, container_port = port.split(':')
			protocol_key = app.ucr_ports_key % container_port + '/protocol'
			protocol_value = updates.get(protocol_key)
			if protocol_value:
				protocol_value = '%s, %s' % (protocol_value, protocol)
			else:
				protocol_value = protocol
			updates[protocol_key] = protocol_value
			updates[app.ucr_ports_key % container_port] = str(host_port)
		if app.auto_mod_proxy and app.has_local_web_interface():
			self.log('Setting ports for apache proxy')
			try:
				min_port = int(ucr_get('appcenter/ports/min'))
			except (TypeError, ValueError):
				min_port = 40000
			try:
				max_port = int(ucr_get('appcenter/ports/max'))
			except (TypeError, ValueError):
				max_port = 41000
			ports_taken = set()
			for app_id, container_port, host_port in app_ports():
				if host_port < max_port:
					ports_taken.add(host_port)
			if app.web_interface_port_http:
				key = app.ucr_ports_key % app.web_interface_port_http
				if key in current_port_config:
					value = current_port_config[key]
				else:
					next_port = currently_free_port_in_range(min_port, max_port, ports_taken)
					ports_taken.add(next_port)
					value = str(next_port)
				updates[key] = value
			if app.web_interface_port_https:
				key = app.ucr_ports_key % app.web_interface_port_https
				if key in current_port_config:
					value = current_port_config[key]
				else:
					next_port = currently_free_port_in_range(min_port, max_port, ports_taken)
					ports_taken.add(next_port)
					value = str(next_port)
				updates[key] = value
		for container_port, host_port in current_port_config.iteritems():
			if container_port in updates:
				if updates[container_port] == host_port:
					updates.pop(container_port)
		if updates:
			# save immediately, no delay: next call needs to know
			# about the (to be) registered ports
			ucr_save(updates)

	def _register_app_report_variables(self, app):
		updates = {}
		for key in ucr_keys():
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

	def _register_overview_variables(self, app):
		updates = {}
		if app.ucs_overview_category is not False:
			for key in ucr_keys():
				if re.match('ucs/web/overview/entries/[^/]+/%s/' % app.id, key):
					updates[key] = None
		if app.ucs_overview_category and app.web_interface:
			self.log('Setting overview variables')
			registry_key = 'ucs/web/overview/entries/%s/%s/%%s' % (app.ucs_overview_category, app.id)
			port_http = app.web_interface_port_http
			port_https = app.web_interface_port_https
			if app.auto_mod_proxy:
				# the port in the ini is not the "public" port!
				# the web interface lives behind our apache with its
				# default ports. but we need to respect disabled ports
				port_http = 80
				port_https = 443
				if app.web_interface_port_http == 0:
					port_http = None
				if app.web_interface_port_https == 0:
					port_https = None

			label = app.get_localised('web_interface_name') or app.get_localised('name')
			label_de = app.get_localised('web_interface_name', 'de') or app.get_localised('name', 'de')
			variables = {
				'icon': os.path.join('/univention/js/dijit/themes/umc/icons/scalable', app.logo_name),
				'port_http': str(port_http or ''),
				'port_https': str(port_https or ''),
				'label': label,
				'label/de': label_de,
				'description': app.get_localised('description'),
				'description/de': app.get_localised('description', 'de'),
				'link': app.web_interface,
			}
			for key, value in variables.iteritems():
				updates[registry_key % key] = value
		return updates

	def _unregister_app(self, app, args, lo=None, pos=None, delay=False):
		if lo is None:
			lo, pos = self._get_ldap_connection(args, allow_machine_connection=True)
		updates = {}
		for key in ucr_keys():
			if key.startswith('appcenter/apps/%s/' % app.id):
				updates[key] = None
			if re.match('ucs/web/overview/entries/[^/]+/%s/' % app.id, key):
				updates[key] = None
			if re.match('appreport/%s/' % app.id, key):
				updates[key] = None
		if app.docker and not app.plugin_of:
			try:
				from univention.appcenter.actions.service import Service
			except ImportError:
				# univention-appcenter-docker is not installed
				pass
			else:
				try:
					init_script = Service.get_init(app)
					os.unlink(init_script)
					self._call_script('/usr/sbin/update-rc.d', os.path.basename(init_script), 'remove')
				except OSError:
					pass
		ldap_object = get_app_ldap_object(app, lo, pos)
		if ldap_object:
			self.log('Removing localhost from LDAP object')
			ldap_object.remove_localhost()
		if not delay:
			ucr_save(updates)
			self._reload_apache()
		return updates

	def _register_installed_apps_in_ucr(self):
		installed_codes = []
		for app in Apps().get_all_apps():
			if app.is_installed():
				installed_codes.append(app.code)
		with catch_stdout(self.logger):
			ucr_save({
				'appcenter/installed': '-'.join(installed_codes),
				'repository/app_center/installed': '-'.join(installed_codes),  # to be deprecated
			})
