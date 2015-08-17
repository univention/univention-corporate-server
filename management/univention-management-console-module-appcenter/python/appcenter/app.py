#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  Application class
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
from glob import glob
import re
from ConfigParser import RawConfigParser, NoOptionError, NoSectionError
from copy import copy
from locale import getlocale
from cgi import escape as cgi_escape
from distutils.version import LooseVersion
import platform
from inspect import getargspec

from univention.config_registry import ConfigRegistry
from univention.lib.package_manager import PackageManager

from univention.appcenter.log import get_base_logger
from univention.appcenter.meta import UniventionMetaClass, UniventionMetaInfo
from univention.appcenter.utils import mkdir, get_current_ram_available, _

CACHE_DIR = '/var/cache/univention-appcenter'
LOCAL_ARCHIVE = '/usr/share/univention-appcenter/archives/all.tar.gz'
SHARE_DIR = '/usr/share/univention-appcenter/apps'
DATA_DIR = '/var/lib/appcenter/app'
CONTAINER_SCRIPTS_PATH = '/usr/share/univention-docker-container-mode/'

app_logger = get_base_logger().getChild('apps')

class Requirement(UniventionMetaInfo):
	save_as_list = '_requirements'
	auto_set_name = True
	pop = True

	def __init__(self, actions, hard, func):
		self.actions = actions
		self.hard = hard
		self.func = func

	def test(self, app, function, package_manager, ucr):
		method = getattr(app, self.name)
		kwargs = {}
		arguments = getargspec(method).args[1:] # remove self
		if 'function' in arguments:
			kwargs['function'] = function
		if 'package_manager' in arguments:
			kwargs['package_manager'] = package_manager
		if 'ucr' in arguments:
			kwargs['ucr'] = ucr
		return method(**kwargs)

	def contribute_to_class(self, klass, name):
		super(Requirement, self).contribute_to_class(klass, name)
		setattr(klass, name, self.func)

def hard_requirement(*actions):
	return lambda func: Requirement(actions, True, func)

def soft_requirement(*actions):
	return lambda func: Requirement(actions, False, func)

class AppAttribute(UniventionMetaInfo):
	save_as_list = '_attrs'
	auto_set_name = True

	def __init__(self, required=False, default=None, regex=None, choices=None, escape=True, localizable=False, strict=True):
		super(AppAttribute, self).__init__()
		self.regex = regex
		self.default = default
		self.required = required
		self.choices = choices
		self.escape = escape
		self.localizable = localizable
		self.strict = strict

	def test_regex(self, regex, value):
		if value is not None and not re.match(regex, value):
			raise ValueError('Invalid format')

	def test_choices(self, value):
		if value is not None and value not in self.choices:
			raise ValueError('Not allowed')

	def test_required(self, value):
		if value is None:
			raise ValueError('Value required')

	def test_type(self, value, instance_type):
		if value is not None:
			if instance_type is None:
				instance_type = basestring
			if not isinstance(value, instance_type):
				raise ValueError('Wrong type')

	def parse_with_ini_file(self, value, ini_file):
		return self.parse(value)

	def test(self, value):
		try:
			if self.required:
				self.test_required(value)
			self.test_type(value, basestring)
			if self.choices:
				self.test_choices(value)
			if self.regex:
				self.test_regex(self.regex, value)
		except ValueError as e:
			if self.strict:
				raise
			else:
				app_logger.warn(str(e))

	def parse(self, value):
		if self.escape and value:
			value = cgi_escape(value)
		return value

	def get(self, value, ini_file):
		if value is None:
			value = copy(self.default)
		try:
			value = self.parse_with_ini_file(value, ini_file)
		except ValueError as exc:
			raise ValueError('%s: %s (%r): %s' % (ini_file, self.name, value, exc))
		else:
			self.test(value)
			return value

class AppBooleanAttribute(AppAttribute):
	def test_type(self, value, instance_type):
		super(AppBooleanAttribute, self).test_type(value, bool)

	def parse(self, value):
		if value in [True, False]:
			return value
		if value is not None:
			value = RawConfigParser._boolean_states.get(str(value).lower())
			if value is None:
				raise ValueError('Invalid value')
		return value

class AppIntAttribute(AppAttribute):
	def test_type(self, value, instance_type):
		super(AppIntAttribute, self).test_type(value, int)

	def parse(self, value):
		if value is not None:
			return int(value)

class AppListAttribute(AppAttribute):
	def parse(self, value):
		if isinstance(value, basestring):
			value = re.split('\s*,\s*', value)
		if value is None:
			value = []
		return value

	def test_required(self, value):
		if not value:
			raise ValueError('Value required')

	def test_type(self, value, instance_type):
		super(AppListAttribute, self).test_type(value, list)

	def test_choices(self, value):
		if not value:
			return
		for val in value:
			super(AppListAttribute, self).test_choices(val)

	def test_regex(self, regex, value):
		if not value:
			return
		for val in value:
			super(AppListAttribute, self).test_regex(regex, value)

class AppAttributeOrFalse(AppBooleanAttribute):
	def parse(self, value):
		try:
			boolean_value = super(AppAttributeOrFalse, self).parse(value)
		except ValueError:
			if value:
				return value
			return False
		else:
			if boolean_value is True:
				return value
			return boolean_value

	def test_choices(self, value):
		if value is False:
			return
		super(AppAttributeOrFalse, self).test_choices(value)

	def test_type(self, value, instance_type):
		try:
			super(AppAttributeOrFalse, self).test_type(value, bool)
		except ValueError:
			super(AppBooleanAttribute, self).test_type(value, None)

class AppFileAttribute(AppAttribute):
	def __init__(self, required=False, default=None, regex=None, choices=None, escape=False, localizable=True):
		# escape=False, localizable=True !
		super(AppFileAttribute, self).__init__(required, default, regex, choices, escape, localizable)

	def parse_with_ini_file(self, value, ini_file):
		filename = self.get_filename(ini_file)
		if filename:
			with open(filename, 'rb') as fhandle:
				value = ''.join(fhandle.readlines()).strip()
		return super(AppFileAttribute, self).parse_with_ini_file(value, ini_file)

	def get_filename(self, ini_file):
		directory = os.path.dirname(ini_file)
		component_id = os.path.splitext(os.path.basename(ini_file))[0]
		fname = self.name.upper()
		localised_file_exts = [fname, '%s_EN' % fname]
		if self.localizable:
			locale = getlocale()[0]
			if locale:
				locale = locale.split('_', 1)[0].upper()
				localised_file_exts.insert(0, '%s_%s' % (fname, locale))
		for localised_file_ext in localised_file_exts:
			filename = os.path.join(directory, '%s.%s' % (component_id, localised_file_ext))
			if os.path.exists(filename):
				return filename

class AppDockerScriptAttribute(AppAttribute):
	def set_name(self, name):
		self.default = os.path.join(CONTAINER_SCRIPTS_PATH, name[14:])
		super(AppDockerScriptAttribute, self).set_name(name)

class App(object):
	__metaclass__ = UniventionMetaClass

	id = AppAttribute(regex='^[a-zA-Z0-9]+(([a-zA-Z0-9-_]+)?[a-zA-Z0-9])?$', required=True)
	code = AppAttribute(regex='^[A-Za-z0-9]{2}$', required=True)
	component_id = AppAttribute(required=True)

	name = AppAttribute(required=True, localizable=True)
	version = AppAttribute(required=True)
	description = AppAttribute(localizable=True)
	long_description = AppAttribute(escape=False, localizable=True)
	screenshot = AppAttribute() # localizable=True
	categories = AppListAttribute(choices=['Administration', 'Business', 'Collaboration', 'Education', 'System services', 'UCS components', 'Virtualization', ''], strict=False)

	website = AppAttribute(localizable=True)
	support_url = AppAttribute(localizable=True)
	contact = AppAttribute()
	vendor = AppAttribute()
	website_vendor = AppAttribute(localizable=True)
	maintainer = AppAttribute()
	website_maintainer = AppAttribute(localizable=True)

	license_agreement = AppFileAttribute()
	readme = AppFileAttribute()
	readme_install = AppFileAttribute()
	readme_post_install = AppFileAttribute()
	readme_update = AppFileAttribute()
	readme_post_update = AppFileAttribute()
	readme_uninstall = AppFileAttribute()
	readme_post_uninstall = AppFileAttribute()

	notify_vendor = AppBooleanAttribute(default=True)
	notification_email = AppAttribute()

	web_interface = AppAttribute()
	web_interface_name = AppAttribute()
	web_interface_port_http = AppIntAttribute(default=80)
	web_interface_port_https = AppIntAttribute(default=443)
	auto_mod_proxy = AppBooleanAttribute(default=True)
	ucs_overview_category = AppAttributeOrFalse(default='services', choices=['admin', 'services'])

	conflicted_apps = AppListAttribute()
	required_apps = AppListAttribute()
	conflicted_system_packages = AppListAttribute()
	required_ucs_version = AppAttribute(regex=r'^(\d+)\.(\d+)-(\d+)(?: errata(\d+))?$')
	end_of_life = AppBooleanAttribute()

	default_packages = AppListAttribute()
	default_packages_master = AppListAttribute()

	umc_module_name = AppAttribute()
	umc_module_flavor = AppAttribute()

	user_activation_required = AppBooleanAttribute()

	ports_exclusive = AppListAttribute(regex='^\d+$')
	ports_redirection = AppListAttribute(regex='^\d+:\d+$')

	server_role = AppListAttribute(default=['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'], choices=['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'])
	supported_architectures = AppListAttribute(default=['amd64', 'i386'], choices=['amd64', 'i386'])
	min_physical_ram = AppIntAttribute(default=0)

	use_shop = AppBooleanAttribute(localizable=True)
	shop_url = AppAttribute(localizable=True)

	ad_member_issue_hide = AppBooleanAttribute()
	ad_member_issue_password = AppBooleanAttribute()

	docker = AppBooleanAttribute()
	docker_image = AppAttribute()
	docker_volumes = AppListAttribute()
	docker_server_role = AppAttribute(default='memberserver', choices=['memberserver', 'domaincontroller_slave'])
	docker_auto_update = AppAttribute(choices=[None, 'packages', 'release'])
	docker_script_init = AppAttribute(default='/sbin/init')
	docker_script_setup = AppDockerScriptAttribute()
	docker_script_store_data = AppDockerScriptAttribute()
	docker_script_restore_data_before_setup = AppDockerScriptAttribute()
	docker_script_restore_data_after_setup = AppDockerScriptAttribute()
	docker_script_update_available = AppDockerScriptAttribute()
	docker_script_update_packages = AppDockerScriptAttribute()
	docker_script_update_release = AppDockerScriptAttribute()
	docker_script_update_app_version = AppDockerScriptAttribute()

	def __init__(self, **kwargs):
		for attr in self._attrs:
			setattr(self, attr.name, kwargs.get(attr.name))
		if self.docker:
			self.supported_architectures = ['amd64']

	def get_docker_image_name(self):
		image = self.docker_image
		if image is None:
			#ucr = ConfigRegistry()
			#ucr.load()
			#version = '%s-%s' % (ucr.get('version/version'), ucr.get('version/patchlevel'))
			#if self.docker_server_role == 'memberserver':
			#	role = 'member'
			#else:
			#	role = 'slave'
			#arch = 'amd64'
			#image = 'univention/ucs-%(role)s-%(arch)s:%(version)s' % {'role': role, 'arch': arch, 'version': version}
			image = 'univention/ucs-appbox-amd64:4.0-0-minbase'
		return image

	def has_local_web_interface(self):
		if self.web_interface:
			return self.web_interface.startswith('/')

	def __str__(self):
		return '%s=%s' % (self.id, self.version)

	def __repr__(self):
		return 'App(id="%s" version="%s")' % (self.id, self.version)

	@classmethod
	def from_ini(cls, ini_file, locale=True):
		app_logger.debug('Loading app from %s' % ini_file)
		if locale is True:
			locale = getlocale()[0]
			if locale:
				locale = locale.split('_', 1)[0]
		config_parser = RawConfigParser()
		with open(ini_file, 'rb') as f:
			config_parser.readfp(f)
		attr_values = {}
		for attr in cls._attrs:
			value = None
			if attr.name == 'component_id':
				value = os.path.splitext(os.path.basename(ini_file))[0]
			else:
				ini_attr_name = attr.name.replace('_', '')
				try:
					if not attr.localizable or not locale:
						raise NoOptionError(ini_attr_name, locale)
					value = config_parser.get(locale, ini_attr_name)
				except (NoSectionError, NoOptionError):
					try:
						value = config_parser.get('Application', ini_attr_name)
					except (NoSectionError, NoOptionError):
						pass
			try:
				value = attr.get(value, ini_file)
			except ValueError as e:
				app_logger.error('Ignoring %s because of %s: %s' % (ini_file, attr.name, e))
				return
			attr_values[attr.name] = value
		return cls(**attr_values)

	@property
	def icon(self):
		return 'apps-%s.png' % self.component_id

	@property
	def ucr_status_key(self):
		return 'appcenter/apps/%s/status' % self.id

	@property
	def ucr_version_key(self):
		return 'appcenter/apps/%s/version' % self.id

	@property
	def ucr_container_key(self):
		return 'appcenter/apps/%s/container' % self.id

	@property
	def ucr_hostdn_key(self):
		return 'appcenter/apps/%s/hostdn' % self.id

	@property
	def ucr_ip_key(self):
		return 'appcenter/apps/%s/ip' % self.id

	@property
	def ucr_ports_key(self):
		return 'appcenter/apps/%s/ports/%%d' % self.id

	def is_installed(self):
		ucr = ConfigRegistry()
		ucr.load()
		return ucr.get(self.ucr_status_key) in ['installed', 'stalled'] and ucr.get(self.ucr_version_key) == self.version

	def get_share_dir(self):
		return os.path.join(SHARE_DIR, self.id)

	def get_share_file(self, ext):
		return os.path.join(self.get_share_dir(), '%s.%s' % (self.id, ext))

	def get_data_dir(self):
		return os.path.join(DATA_DIR, self.id, 'data')

	def get_conf_dir(self):
		return os.path.join(DATA_DIR, self.id, 'conf')

	def get_conf_file(self, fname):
		if fname.startswith('/'):
			fname = fname[1:]
		fname = os.path.join(self.get_conf_dir(), fname)
		if not os.path.exists(fname):
			mkdir(os.path.dirname(fname))
		return fname

	def get_cache_file(self, ext):
		return os.path.join(CACHE_DIR, '%s.%s' % (self.component_id, ext))

	def get_ini_file(self):
		return self.get_cache_file('ini')

	def get_localised(self, key, loc=None):
		from univention.appcenter import get_action
		get = get_action('get')()
		keys = [(loc, key)]
		for section, name, value in get.get_values(self, keys, warn=False):
			return value

	def get_localised_list(self, key, loc=None):
		from univention.appcenter import get_action
		get = get_action('get')()
		ret = []
		key = key.replace('_', '').lower()
		keys = [(None, key), ('de', key)]
		for section, name, value in get.get_values(self, keys, warn=False):
			if value is None:
				continue
			if section is None:
				section = 'en'
			value = '[%s] %s' % (section, value)
			ret.append(value)
		return ret

	@hard_requirement('install', 'upgrade')
	def must_have_fitting_ucs_version(self, ucr):
		required_version = self.required_ucs_version
		if not required_version:
			return True
		version_bits = re.match(r'^(\d+)\.(\d+)-(\d+)(?: errata(\d+))?$', required_version).groups()
		major, minor = ucr.get('version/version').split('.', 1)
		patchlevel = ucr.get('version/patchlevel')
		errata = ucr.get('version/erratalevel')
		comparisons = zip(version_bits, [major, minor, patchlevel, errata])
		for required, present in comparisons:
			if int(required or 0) > int(present):
				return {'required_version': required_version}
		return True

	@hard_requirement('install', 'upgrade')
	def must_not_be_docker_in_docker(self, ucr):
		'''The application uses a container technology while the system
		itself runs in a container. Using the application is not
		supported on this host'''
		return not self.docker or not ucr.get('docker/container/uuid')

	@hard_requirement('install', 'upgrade')
	def must_have_valid_license(self, ucr):
		'''For the installation of this application, a UCS license key
		with a key identification (Key ID) is required'''
		if self.notify_vendor:
			return ucr.get('uuid/license') is not None
		return True

	@hard_requirement('install')
	def must_not_be_installed(self):
		'''This application is already installed'''
		return not self.is_installed()

	@hard_requirement('install')
	def must_not_be_end_of_life(self):
		'''This application was discontinued and may not be installed
		anymore'''
		return not self.end_of_life

	@hard_requirement('install', 'upgrade')
	def must_have_supported_architecture(self):
		'''This application only supports %(supported)s as
		architecture. %(msg)s'''
		supported_architectures = self.supported_architectures
		platform_bits = platform.architecture()[0]
		aliases = {'i386': '32bit', 'amd64': '64bit'}
		if supported_architectures:
			for architecture in supported_architectures:
				if aliases[architecture] == platform_bits:
					break
			else:
				# For now only two architectures are supported:
				#   32bit and 64bit - and this will probably not change
				#   too soon.
				# So instead of returning lists and whatnot
				#   just return a nice message
				# Needs to be adapted when supporting different archs
				supported = supported_architectures[0]
				if supported == 'i386':
					needs = 32
					has = 64
				else:
					needs = 64
					has = 32
				msg = _('The application needs a %(needs)s-bit operating system. This server is running a %(has)s-bit operating system.') % {'needs': needs, 'has': has}
				return {'supported': supported, 'msg': msg}
		return True

	@hard_requirement('install', 'upgrade')
	def must_be_joined_if_master_packages(self):
		'''This application requires an extension of the LDAP schema'''
		is_joined = os.path.exists('/var/univention-join/joined')
		return bool(is_joined or not self.default_packages_master)

	@hard_requirement('install', 'upgrade', 'uninstall')
	def must_not_have_concurrent_operation(self, package_manager):
		'''Another package operation is in progress'''
		if self.docker:
			return True
		else:
			return package_manager.progress_state._finished # TODO: package_manager.is_finished()

	@hard_requirement('install', 'upgrade')
	def must_have_correct_server_role(self, ucr):
		'''The application cannot be installed on the current server
		role (%(current_role)s). In order to install the application,
		one of the following roles is necessary: %(allowed_roles)r'''
		server_role = ucr.get('server/role')
		if not self._allowed_on_local_server(ucr):
			return {
				'current_role' : server_role,
				'allowed_roles' : ', '.join(self.server_role),
			}
		return True

	@hard_requirement('install', 'upgrade')
	def must_have_no_conflicts_packages(self, package_manager):
		'''The application conflicts with the following packages: %r'''
		conflict_packages = []
		for pkgname in self.conflicted_system_packages:
			if package_manager.is_installed(pkgname):
				conflict_packages.append(pkgname)
		if conflict_packages:
			return conflict_packages
		return True

	@hard_requirement('install', 'upgrade')
	def must_have_no_conflicts_apps(self, ucr):
		'''The application conflicts with the following applications:
			%r'''
		conflictedapps = []
		for app in AppManager.get_all_apps():
			if not app._allowed_on_local_server(ucr):
				# cannot be installed, continue
				continue
			if app.id in self.conflicted_apps or self.id in app.conflicted_apps:
				if app.is_installed():
					conflictedapps.append({'id': app.id, 'name': app.name})
		if conflictedapps:
			return conflictedapps
		return True

	@hard_requirement('install', 'upgrade')
	def must_have_no_unmet_dependencies(self):
		'''The application requires the following applications: %r'''
		unmet_packages = []
		for app in AppManager.get_all_apps():
			if app.id in self.required_apps:
				if not app.is_installed():
					unmet_packages.append({'id': app.id, 'name': app.name})
		if unmet_packages:
			return unmet_packages
		return True

	@hard_requirement('uninstall')
	def must_not_be_depended_on(self):
		'''The application is required for the following applications
		to work: %r'''
		depending_apps = []
		for app in AppManager.get_all_apps():
			if self.id in app.required_apps and app.is_installed():
				depending_apps.append({'id': app.id, 'name': app.name})
		if depending_apps:
			return depending_apps
		return True

	@soft_requirement('install', 'upgrade')
	def shall_have_enough_ram(self, function):
		'''The application requires %(minimum)d MB of free RAM but only
		%(current)d MB are available.'''
		current_ram = get_current_ram_available()
		required_ram = self.min_physical_ram
		if function == 'upgrade':
			# is already installed, just a minor version upgrade
			#   RAM "used" by this installed app should count
			#   as free. best approach: substract it
			installed_app = AppManager.find(self)
			old_required_ram = installed_app.min_physical_ram
			required_ram = required_ram - old_required_ram
		if current_ram < required_ram:
			return {'minimum': required_ram, 'current': current_ram}
		return True

	@soft_requirement('install', 'upgrade')
	def shall_only_be_installed_in_ad_env_with_password_service(self, ucr):
		'''The application requires the password service to be set up
		on the Active Directory domain controller server.'''
		return not self._has_active_ad_member_issue(ucr, 'password')

	def check(self, function):
		package_manager = AppManager.get_package_manager()
		ucr = ConfigRegistry()
		ucr.load()
		hard_problems = {}
		soft_problems = {}
		for requirement in self._requirements:
			if function not in requirement.actions:
				continue
			app = self
			if function == 'upgrade':
				app = AppManager.find(self)
				if app > self:
					# upgrade is not possible,
					#   special handling
					hard_problems['must_have_candidate'] = False
					continue
			result = requirement.test(app, function, package_manager, ucr)
			if result is not True:
				if requirement.hard:
					hard_problems[requirement.name] = result
				else:
					soft_problems[requirement.name] = result
		return hard_problems, soft_problems

	def _allowed_on_local_server(self, ucr):
		server_role = ucr.get('server/role')
		allowed_roles = self.server_role
		return not allowed_roles or server_role in allowed_roles

	def _has_active_ad_member_issue(self, ucr, issue):
		return ucr.is_true('ad/member') and getattr(self, 'ad_member_issue_%s' % issue, False)

	def __cmp__(self, other):
		return cmp(self.id, other.id) or cmp(LooseVersion(self.version), LooseVersion(other.version))

class AppManager(object):
	_cache = []
	_package_manager = None

	@classmethod
	def clear_cache(cls):
		cls._cache[:] = []

	@classmethod
	def _get_every_single_app(cls):
		if not cls._cache:
			for ini in glob(os.path.join(CACHE_DIR, '*.ini')):
				app = App.from_ini(ini)
				if app is not None:
					cls._cache.append(app)
			cls._cache.sort()
		return cls._cache

	@classmethod
	def get_all_apps(cls):
		ret = []
		ids = set()
		for app in cls._get_every_single_app():
			ids.add(app.id)
		for app_id in sorted(ids):
			ret.append(cls.find(app_id))
		return ret

	@classmethod
	def get_all_locally_installed_apps(cls):
		ret = []
		for app in cls._get_every_single_app():
			if app.is_installed():
				ret.append(app)
		return ret

	@classmethod
	def find_by_component_id(cls, component_id):
		for app in cls._get_every_single_app():
			if app.component_id == component_id:
				return app

	@classmethod
	def get_all_apps_with_id(cls, app_id):
		ret = []
		for app in cls._get_every_single_app():
			if app.id == app_id:
				ret.append(app)
		return ret

	@classmethod
	def find(cls, app_id, app_version=None, latest=False):
		if isinstance(app_id, App):
			app_id = app_id.id
		apps = cls.get_all_apps_with_id(app_id)
		if app_version:
			for app in apps:
				if app.version == app_version:
					return app
		elif not latest:
			for app in apps:
				if app.is_installed():
					return app
		if apps:
			return apps[-1]

	@classmethod
	def get_package_manager(cls):
		if cls._package_manager is None:
			cls._package_manager = PackageManager(lock=False)
			cls._package_manager.set_finished() # currently not working. accepting new tasks
			cls._package_manager.logger.parent = get_base_logger()
		return cls._package_manager

	@classmethod
	def set_package_manager(cls, package_manager):
		cls._package_manager = package_manager

	@classmethod
	def get_server(cls):
		ucr = ConfigRegistry()
		ucr.load()
		server = ucr.get('repository/app_center/server', 'appcenter.software-univention.de')
		if not server.startswith('http'):
			server = 'https://%s' % server
		return server

