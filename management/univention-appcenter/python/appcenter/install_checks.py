#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for uninstalling an app
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2015-2022 Univention GmbH
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
import os
import platform

from six import with_metaclass

from univention.appcenter.app import LooseVersion
from univention.appcenter.meta import UniventionMetaClass
from univention.appcenter.ucr import ucr_get, ucr_load, ucr_is_true
from univention.appcenter.app_cache import Apps
from univention.appcenter.utils import get_current_ram_available, get_free_disk_space, underscore, container_mode, app_ports, _
from univention.appcenter.actions import get_action
from univention.appcenter.packages import packages_are_installed, get_package_manager


_REQUIREMENTS = {}


class RequirementMetaClass(UniventionMetaClass):
	def __new__(mcs, name, bases, attrs):
		new_cls = super(RequirementMetaClass, mcs).__new__(mcs, name, bases, attrs)
		if new_cls.__doc__:
			_REQUIREMENTS[new_cls.get_name()] = new_cls
		return new_cls


class Requirement(with_metaclass(RequirementMetaClass)):
	def __init__(self, apps, action):
		self.apps = apps
		self.action = action

	def test(self):
		if self.action == 'install':
			return self._test_install()
		elif self.action == 'upgrade':
			return self._test_upgrade()
		elif self.action == 'remove':
			return self._test_remove()
		return {}

	def _test_install(self):
		return {}

	def _test_upgrade(self):
		return {}

	def _test_remove(self):
		return {}

	@classmethod
	def get_name(cls):
		return underscore(cls.__name__)

	def other_apps(self, app):
		return [_app for _app in self.apps if app != _app]


class SingleRequirement(Requirement):
	def _test_install(self):
		ret = {}
		for app in self.apps:
			result = self.test_install(app)
			if result is not None and result is not True:
				ret[app.id] = result
		return ret

	def test_install(self, app):
		pass

	def _test_upgrade(self):
		ret = {}
		for app in self.apps:
			result = self.test_upgrade(app)
			if result is not None and result is not True:
				ret[app.id] = result
		return ret

	def test_upgrade(self, app):
		pass

	def _test_remove(self):
		ret = {}
		for app in self.apps:
			result = self.test_remove(app)
			if result is not None and result is not True:
				ret[app.id] = result
		return ret

	def test_remove(self, app):
		pass


class MultiRequirement(Requirement):
	def _test_install(self):
		ret = {}
		result = self.test_install(self.apps)
		if result is not None and result is not True:
			ret['__all__'] = result
		return ret

	def test_install(self, apps):
		pass

	def _test_upgrade(self):
		ret = {}
		result = self.test_upgrade(self.apps)
		if result is not None and result is not True:
			ret['__all__'] = result
		return ret

	def test_upgrade(self, apps):
		pass

	def _test_remove(self):
		ret = {}
		result = self.test_remove(self.apps)
		if result is not None and result is not True:
			ret['__all__'] = result
		return ret

	def test_remove(self, apps):
		pass


class HardRequirement(object):
	def is_error(self):
		return True


class SoftRequirement(object):
	def is_error(self):
		return False


class MustHaveCorrectServerRole(SingleRequirement, HardRequirement):
	'''The application cannot be installed on the current server
		role (%(current_role)s). In order to install the application,
		one of the following roles is necessary: %(allowed_roles)r'''
	def test_install(self, app):
		server_role = ucr_get('server/role')
		if not app._allowed_on_local_server():
			return {
				'current_role': server_role,
				'allowed_roles': ', '.join(app.server_role),
			}

	test_upgrade = test_install


class MustHaveFittingAppVersion(SingleRequirement, HardRequirement):
	'''To upgrade, at least version %(required_version)s needs to
		be installed.'''
	def test_upgrade(self, app):
		if app.required_app_version_upgrade:
			required_version = LooseVersion(app.required_app_version_upgrade)
			installed_app = Apps().find(app.id)
			installed_version = LooseVersion(installed_app.version)
			if required_version > installed_version:
				return {'required_version': app.required_app_version_upgrade}


class MustHaveFittingKernelVersion(MultiRequirement, HardRequirement):
	'''The Kernel version has to be upgraded and the system rebootet.'''
	def test_install(self, apps):
		if any(app.docker for app in apps):
			kernel = LooseVersion(os.uname()[2])
			if kernel < LooseVersion('4.9'):
				return False

	test_upgrade = test_install


class MustHaveCandidate(SingleRequirement, HardRequirement):
	'''The application is either not installed or no newer version is available'''
	def test_upgrade(self, app):
		_app = Apps().find(app.id)
		if not _app.is_installed() or _app >= app:
			return False


class MustHaveFittingUcsVersion(SingleRequirement, HardRequirement):
	'''The application requires UCS version %(required_version)s.'''
	def test_install(self, app):
		required_ucs_version = None
		for supported_version in app.supported_ucs_versions:
			if supported_version.startswith('%s-' % ucr_get('version/version')):
				required_ucs_version = supported_version
				break
		else:
			if app.get_ucs_version() == ucr_get('version/version'):
				if app.required_ucs_version:
					required_ucs_version = app.required_ucs_version
				else:
					return True
		if required_ucs_version is None:
			return {'required_version': app.get_ucs_version()}
		major, minor = ucr_get('version/version').split('.', 1)
		patchlevel = ucr_get('version/patchlevel')
		errata = ucr_get('version/erratalevel')
		version_bits = re.match(r'^(\d+)\.(\d+)-(\d+)(?: errata(\d+))?$', required_ucs_version).groups()
		comparisons = zip(version_bits, [major, minor, patchlevel, errata])
		for required, present in comparisons:
			if int(required or 0) > int(present):
				return {'required_version': required_ucs_version}
			if int(required or 0) < int(present):
				return True

	test_upgrade = test_install


class MustHaveInstallPermissions(SingleRequirement, HardRequirement):
	'''You need to buy the App to install this version.'''
	def test_install(self, app):
		if not app.install_permissions_exist():
			return {'shop_url': app.shop_url, 'version': app.version}

	test_upgrade = test_install


class MustHaveNoConflictsApps(SingleRequirement, HardRequirement):
	'''The application conflicts with the following applications:
			%r'''
	def test_install(self, app):
		conflictedapps = set()
		apps_cache = Apps()
		# check ConflictedApps
		for _app in apps_cache.get_all_apps():
			if not _app._allowed_on_local_server():
				# cannot be installed, continue
				continue
			if _app.id in app.conflicted_apps or app.id in _app.conflicted_apps:
				if _app.is_installed():
					conflictedapps.add(_app.id)
				elif _app in self.other_apps(app):
					conflictedapps.add(_app.id)
		# check port conflicts
		ports = []
		for i in app.ports_exclusive:
			ports.append(i)
		for i in app.ports_redirection:
			ports.append(i.split(':', 1)[0])
		for app_id, container_port, host_port in app_ports():
			if app_id != app.id and str(host_port) in ports:
				conflictedapps.add(app_id)
		for _app in self.other_apps(app):
			other_ports = set()
			for i in _app.ports_exclusive:
				other_ports.add(i)
			for i in _app.ports_redirection:
				other_ports.add(i.split(':', 1)[0])
			if other_ports.intersection(ports):
				conflictedapps.add(_app.id)
		if conflictedapps:
			conflictedapps = [apps_cache.find(app_id) for app_id in conflictedapps]
			return [{'id': _app.id, 'name': _app.name} for _app in conflictedapps if _app]

	test_upgrade = test_install


class MustHaveNoConflictsPackages(SingleRequirement, HardRequirement):
	'''The application conflicts with the following packages: %r'''
	def test_install(self, app):
		conflict_packages = []
		for pkgname in app.conflicted_system_packages:
			if packages_are_installed([pkgname], strict=True):
				conflict_packages.append(pkgname)
		if conflict_packages:
			return conflict_packages

	test_upgrade = test_install


class MustHaveNoUnmetDependencies(SingleRequirement, HardRequirement):
	'''The application requires the following applications: %r'''
	def test_install(self, app):
		unmet_apps = []

		apps_cache = Apps()
		# RequiredApps
		for _app in apps_cache.get_all_apps():
			if _app.id in app.required_apps:
				if not _app.is_installed():
					unmet_apps.append({'id': _app.id, 'name': _app.name, 'in_domain': False})

		# RequiredAppsInDomain
		domain = get_action('domain')
		apps = [apps_cache.find(app_id) for app_id in app.required_apps_in_domain]
		apps_info = domain.to_dict(apps)
		for _app in apps_info:
			if not _app:
				continue
			if not _app['is_installed_anywhere']:
				local_allowed = _app['id'] not in app.conflicted_apps
				unmet_apps.append({'id': _app['id'], 'name': _app['name'], 'in_domain': True, 'local_allowed': local_allowed})
		unmet_apps = [unmet_app for unmet_app in unmet_apps if unmet_app['id'] not in (_app.id for _app in self.other_apps(app))]
		if unmet_apps:
			return unmet_apps

	test_upgrade = test_install


class MustHaveSupportedArchitecture(SingleRequirement, HardRequirement):
	'''This application only supports %(supported)s as
		architecture. %(msg)s'''
	def test_install(self, app):
		supported_architectures = app.supported_architectures
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

	test_upgrade = test_install


class MustHaveValidLicense(MultiRequirement, HardRequirement):
	'''For the installation, a UCS license key
		with a key identification (Key ID) is required'''
	def test_install(self, apps):
		if any(app.notify_vendor for app in apps):
			license = ucr_get('uuid/license')
			if license is None:
				ucr_load()
				license = ucr_get('uuid/license')
			return license is not None

	test_upgrade = test_install


class MustNotBeDependedOn(SingleRequirement, HardRequirement):
	'''The application is required for the following applications
		to work: %r'''
	def test_remove(self, app):
		depending_apps = []

		apps_cache = Apps()
		# RequiredApps
		for _app in apps_cache.get_all_apps():
			if app.id in _app.required_apps and _app.is_installed():
				depending_apps.append({'id': _app.id, 'name': _app.name})

		# RequiredAppsInDomain
		apps = [_app for _app in apps_cache.get_all_apps() if app.id in _app.required_apps_in_domain]
		if apps:
			domain = get_action('domain')
			self_info = domain.to_dict([app])[0]
			hostname = ucr_get('hostname')
			if not any(inst['version'] for host, inst in self_info['installations'].items() if host != hostname):
				# this is the only installation
				apps_info = domain.to_dict(apps)
				for _app in apps_info:
					if _app['is_installed_anywhere']:
						depending_apps.append({'id': _app['id'], 'name': _app['name']})

		depending_apps = [depending_app for depending_app in depending_apps if depending_app['id'] not in (_app.id for _app in self.other_apps(app))]
		if depending_apps:
			return depending_apps


class MustNotBeDockerIfDockerIsDisabled(SingleRequirement, HardRequirement):
	'''The application uses a container technology while the App Center
		is configured to not not support it'''
	def test_install(self, app):
		return not app.docker or ucr_is_true('appcenter/docker', True)

	test_upgrade = test_install


class MustNotBeDockerInDocker(SingleRequirement, HardRequirement):
	'''The application uses a container technology while the system
		itself runs in a container. Using the application is not
		supported on this host'''
	def test_install(self, app):
		return not app.docker or not container_mode()

	test_upgrade = test_install


class MustNotBeEndOfLife(SingleRequirement, HardRequirement):
	'''This application was discontinued and may not be installed
		anymore'''
	def test_install(self, app):
		return not app.end_of_life


class MustNotBeInstalled(SingleRequirement, HardRequirement):
	'''This application is already installed'''
	def test_install(self, app):
		return not app.is_installed()


class MustNotBeVoteForApp(SingleRequirement, HardRequirement):
	'''The application is not yet installable. Vote for this app
		now and bring your favorite faster to the Univention App
		Center'''
	def test_install(self, app):
		return not app.vote_for_app

	test_upgrade = test_install


class MustNotHaveConcurrentOperation(SingleRequirement, HardRequirement):
	'''Another package operation is in progress'''
	def test_install(self, app):
		if app.docker:
			return True
		else:
			return get_package_manager().progress_state._finished  # TODO: package_manager.is_finished()

	test_upgrade = test_install

	test_remove = test_install


class ShallHaveEnoughFreeDiskSpace(MultiRequirement, SoftRequirement):
	'''The system needs %(minimum)d MB of free disk space but only
		%(current)d MB are available.'''
	def test_install(self, apps):
		required_free_disk_space = 0
		for app in apps:
			required_free_disk_space += (app.min_free_disk_space or 0)
		if required_free_disk_space <= 0:
			return True
		current_free_disk_space = get_free_disk_space()
		if current_free_disk_space and current_free_disk_space < required_free_disk_space:
			return {'minimum': required_free_disk_space, 'current': current_free_disk_space}


class ShallHaveEnoughRam(MultiRequirement, SoftRequirement):
	'''The system need at least %(minimum)d MB of free RAM but only
		%(current)d MB are available.'''
	def test_install(self, apps):
		current_ram = get_current_ram_available()
		required_ram = 0
		for app in apps:
			required_ram += app.min_physical_ram
		if current_ram < required_ram:
			return {'minimum': required_ram, 'current': current_ram}

	def test_upgrade(self, apps):
		current_ram = get_current_ram_available()
		required_ram = 0
		for app in apps:
			required_ram += app.min_physical_ram
			installed_app = Apps().find(app.id)
			# is already installed, just a minor version upgrade
			#   RAM "used" by this installed app should count
			#   as free. best approach: subtract it
			required_ram -= installed_app.min_physical_ram
		if current_ram < required_ram:
			return {'minimum': required_ram, 'current': current_ram}


class ShallNotBeDockerIfDiscouraged(SingleRequirement, HardRequirement):
	'''The application has not been approved to migrate all
		existing data. Maybe there is a migration guide:
		%(migration_link)s'''
	def test_install(self, app):
		problem = app._docker_prudence_is_true() and not app.docker_migration_works
		if problem:
			return {'migration_link': app.docker_migration_link}

	test_upgrade = test_install


class ShallOnlyBeInstalledInAdEnvWithPasswordService(SingleRequirement, SoftRequirement):
	'''The application requires the password service to be set up
		on the Active Directory domain controller server.'''
	def test_install(self, app):
		return not app._has_active_ad_member_issue('password')

	test_upgrade = test_install


def check(apps, action):
	errors = {}
	warnings = {}
	for name, klass in _REQUIREMENTS.items():
		requirement = klass(apps, action)
		result = requirement.test()
		if result:
			if requirement.is_error():
				errors[name] = result
			else:
				warnings[name] = result
	return errors, warnings


def get_requirement(name):
	return _REQUIREMENTS[name]
