# -*- coding: utf-8 -*-
#
# UCS test
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2016-2022 Univention GmbH
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

import contextlib
import functools
import itertools
import logging
import os.path
import re
import string
import subprocess
import time

import lxml.html
import requests

import univention.appcenter.log as app_logger
import univention.testing.debian_package as debian_package
import univention.testing.utils as utils
from univention.appcenter.actions import get_action
from univention.appcenter.app_cache import AppCenterCache, Apps
from univention.appcenter.utils import get_local_fqdn
from univention.config_registry import ConfigRegistry
from univention.testing.umc import Client

APPCENTER_FILE = "/var/cache/appcenter-installed.txt"  # installed apps


def restart_umc():
	print('Restarting UMC')
	subprocess.check_call(['systemctl', 'restart', 'univention-management-console-server'])
	time.sleep(3)


def get_requested_apps():
	ret = []
	try:
		with open(APPCENTER_FILE) as f:
			for line in f:
				app = Apps().find(line.strip())
				if app:
					ret.append(app)
				else:
					pass
					# utils.fail('Error finding %s' % (line,))
	except EnvironmentError:
		pass
		# utils.fail('Error reading %s: %s' % (APPCENTER_FILE, exc))
	return ret


class AppCenterOperationError(Exception):
	pass


class AppCenterCheckError(Exception):
	pass


class AppCenterTestFailure(Exception):
	pass


class AppCenterOperations(object):

	def __init__(self):
		self.client = Client.get_test_connection()

	def _error_handler(self, error):
		raise AppCenterOperationError(error)

	def _renew_connection(self):
		try:
			if self.client.umc_get('session-info').status != 200:
				raise ValueError()
		except BaseException:
			self.client.authenticate(self.client.username, self.client.password)

	def query(self):
		self._renew_connection()
		return self.client.umc_command("appcenter/query").result

	def get(self, application):
		self._renew_connection()
		data = {"application": application}
		return self.client.umc_command("appcenter/get", data).result

	def resolve(self, action, apps):
		"""Call the UMC command `appcenter/resolve` with the given arguments."""
		self._renew_connection()
		data = {"action": action, "apps": apps}
		return self.client.umc_command("appcenter/resolve", data).result

	def run(self, args):
		"""Call the UMC command `appcenter/run` with the given options.

		This will request a progress update every 3 seconds via
		`appcenter/progress` und call `callback(info, steps)` if a callback
		function was given and `info` or `steps` changed"""
		self._renew_connection()
		progress_id = self.client.umc_command("appcenter/run", args).result["id"]

		last_title = None

		while True:
			progress = self.client.umc_command("appcenter/progress", {"progress_id": progress_id}, print_request_data=False, print_response=False).result
			if last_title != progress["title"]:
				last_title = progress["title"]
				print(last_title)

			for msg in progress["intermediate"]:
				print("", msg["message"])
			finished = progress.get("finished", False)
			if finished:
				print("*** RESULT ***")
				print(progress["result"])
				return progress["result"]
			time.sleep(3)

	def _make_run_args(self, apps, host=None):
		# missing: dry_run: True / False and action: "install"/"upgrade"/"remove"
		host = host or get_local_fqdn()
		return {
			"apps": apps,
			"auto_installed": [],
			"hosts": {host: apps},
			"settings": {app: {} for app in apps},
		}

	def install_dry_run(self, apps, host=None):
		args = self._make_run_args(apps, host)
		args["action"] = "install"
		args["dry_run"] = True
		return self.run(args)

	def install(self, apps, host=None):
		args = self._make_run_args(apps, host)
		args["action"] = "install"
		args["dry_run"] = False
		return self.run(args)

	def upgrade_dry_run(self, apps, host=None):
		args = self._make_run_args(apps, host)
		args["action"] = "upgrade"
		args["dry_run"] = True
		return self.run(args)

	def upgrade(self, apps, host=None):
		args = self._make_run_args(apps, host)
		args["action"] = "upgrade"
		args["dry_run"] = False
		return self.run(args)

	def remove_dry_run(self, apps, host=None):
		args = self._make_run_args(apps, host)
		args["action"] = "remove"
		args["dry_run"] = True
		return self.run(args)

	def remove(self, apps, host=None):
		args = self._make_run_args(apps, host)
		args["action"] = "remove"
		args["dry_run"] = False
		return self.run(args)

	def is_installed(self, application, info=None, msg=None):
		if info is None:
			info = self.get(application)
		result = info.get("is_installed", False) or info.get("is_installed_anywhere", False)
		if msg and not result:
			raise AppCenterOperationError(msg.format(application))
		return result

	def is_docker(self, application, info=None, msg=None):
		if info is None:
			info = self.get(application)
		result = not info.get("docker_image") is None
		if msg and not result:
			raise AppCenterOperationError(msg.format(application))
		return result

	def update_available(self, application, info=None, msg=None):
		if info is None:
			info = self.get(application)
		result = any(m.get("update_available", False) for m in info.get("installations", {}).values())
		if msg and not result:
			raise AppCenterOperationError(msg.format(application))
		return result


class DebianPackage(debian_package.DebianPackage):

	def __init__(self, name="testdeb", version="1.0", depends=None, breaks=None, conflicts=None):
		self._depends = depends or list()
		self._breaks = breaks or list()
		self._conflicts = conflicts or list()

		# because `DebianPackage` is an old-style class
		debian_package.DebianPackage.__init__(self, name, version)

	@property
	def name(self):
		return self._package_name

	@property
	def version(self):
		return self._package_version

	@property
	def name_version(self):
		return "{} (>= {})".format(self._package_name, self._package_version)

	def create_file(self, name="", buffer=""):
		path = os.path.join(self._package_tempdir, name)
		self.__create_file_from_buffer(path, buffer)
		return path

	def get_all_binary_names(self):
		yield self.get_binary_name()
		for package in self._depends:
			if hasattr(package, "get_binary_name"):
				yield package.get_binary_name()

	def _create_control(self):
		control_template = """
Source: {package_name}
Section: univention
Priority: optional
Maintainer: Univention GmbH <packages@univention.de>
Build-Depends: debhelper
Standards-Version: 3.5.2

Package: {package_name}
Architecture: all
Depends: ${{misc:Depends}}, {depends}
Breaks: {breaks}
Conflicts: {conflicts}
Description: UCS - Test package
 It is part of Univention Corporate Server (UCS), an
 integrated, directory driven solution for managing
 corporate environments. For more information about UCS,
 refer to: https://www.univention.de/
"""  # noqa: E101

		depends = [p.name_version for p in self._depends]
		breaks = [p.name_version for p in self._breaks]
		conflicts = [p.name_version for p in self._conflicts]
		control = control_template.format(package_name=self._package_name, depends=", ".join(depends), breaks=", ".join(breaks), conflicts=", ".join(conflicts))
		self.create_debian_file_from_buffer('control', control)


class AppPackage(object):
	_CODES = itertools.combinations_with_replacement(string.ascii_uppercase, 2)
	CODES = itertools.cycle("".join(code) for code in _CODES)
	COMPONENT_IDS = itertools.count(100, 100)

	def __init__(self, package, ini_items, svg_buffer=""):
		self._package = package
		self._ucs_version = ini_items.get("version")

		my_ini_items = dict(ini_items)
		self.app_id = my_ini_items.get("ID")
		self.app_name = my_ini_items.get("Name")
		self.app_version = my_ini_items.get("Version")
		self.app_code = my_ini_items.get("Code")
		self.debian_name = self._package.name

		svg_file = my_ini_items.setdefault("Logo", "{}_logo.svg".format(self.app_id))
		self._svg_path = self._package.create_file(svg_file, svg_buffer)

		ini_file = "{}.ini".format(self.app_id)
		ini_buffer = self._build_ini_buffer(my_ini_items)
		self._ini_path = self._package.create_file(ini_file, ini_buffer)

		self.populate = get_action("dev-populate-appcenter")

	def _build_ini_buffer(self, ini_items):
		def lines():
			yield "[Application]"
			for (key, value) in ini_items.items():
				yield "{}={}".format(key, value)
		return "\n".join(lines())

	@classmethod
	def from_package(cls, package, app_id=None, app_name=None, app_version="3.14", app_code=None, app_conflicted_apps=None, app_required_apps=None):
		my_app_id = app_id or package.name
		ini_items = {
			"ID": my_app_id,
			"Code": app_code or next(AppPackage.CODES),
			"Version": app_version,
			"Name": app_name or my_app_id,
			"DefaultPackages": package.name,
		}
		if app_required_apps:
			conflicted = ",".join(a.app_id for a in app_required_apps)
			ini_items["RequiredApps"] = conflicted
		if app_conflicted_apps:
			conflicted = ",".join(a.app_id for a in app_conflicted_apps)
			ini_items["ConflictedApps"] = conflicted
		return cls(package, ini_items)

	@classmethod
	def with_package(cls, app_id=None, app_name=None, app_version="3.14", app_code=None, app_conflicted_apps=None, **deb_args):
		package = DebianPackage(**deb_args)
		return cls.from_package(package, app_id, app_name, app_version, app_code)

	def build_and_publish(self, component_id=None):
		self._package.build()
		if component_id is None:
			component_id = "{}_{}".format(self.app_id, next(AppPackage.COMPONENT_IDS))

		msg = "Publishing {} (code={}, version={}, component-id={})"
		print(msg.format(self.app_id, self.app_code, self.app_version, component_id))

		self.populate.call(new=True, ini=self._ini_path, logo=self._svg_path, component_id=component_id, packages=list(self._package.get_all_binary_names()))

	def remove_tempdir(self):
		self._package.remove()


class CheckOperations(object):

	def __init__(self, application, info):
		self.application = application
		self.info = info
		self.ucr = ConfigRegistry()
		self.ucr.load()

	@classmethod
	def installed(cls, application, info):
		print("Running checks if correctly installed..")
		checks = cls(application, info)
		return all((
			checks._check_dpkg_installed_status(),
			checks._check_ucr_variables_exist(),
			checks._check_files_exist(),
			checks._check_ldap_object_exists(),
			checks._check_url_accessible()
		))

	@classmethod
	def uninstalled(cls, application, info):
		print("Running checks if correctly uninstalled..")
		checks = cls(application, info)
		return all((
			checks._check_dpkg_uninstalled_status(),
			checks._check_ucr_variables_dont_exist(),
			checks._check_ldap_object_doesnt_exist()
		))

	def _fail(self, message):
		msg = "Error in (un)installed checks for {}: {}"
		print(msg.format(self.application, message))
		return False

	def _packages(self):
		for package in self.info.get("default_packages", list()):
			yield package
		master = ("domaincontroller_master", "domaincontroller_backup")
		if self.ucr.get("server/role") in master:
			for package in self.info.get("default_packages_master", list()):
				yield package

	def _dpkg_status(self, package):
		cmd = ["dpkg-query", "-f='${db:Status-Abbrev}xx'", "--show", package]
		output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
		(expected_char, current_char) = output[:2]
		expected = {"u": "unknown", "i": "install", "h": "hold", "r": "remove", "p": "purge"}.get(expected_char, "unknown")
		current = {"n": "not-installed", "c": "config-files", "U": "unpacked", "H": "half-installed", "F": "half-configured", "W": "triggers-awaited", "t": "tritters-pending", "i": "installed"}.get(current_char, "unknown")
		return (expected, current)

	def _get_dn(self):
		app_version = self.info.get("version")
		ldap_base = self.ucr.get("ldap/base")
		dn = "univentionAppID={id}_{version},cn={id},cn=apps,cn=univention,{base}"
		return dn.format(id=self.application, version=app_version, base=ldap_base)

	def _check_url(self, protocol, port, interface):
		fqdn = '{}.{}'.format(self.ucr.get("hostname"), self.ucr.get("domainname"))
		url = "{}://{}:{}{}".format(protocol, fqdn, port, interface)
		response = requests.get(url, timeout=30, verify=False)

		try:
			response.raise_for_status()
		except requests.HTTPError:
			return self._fail("webinterface at {} not reachable".format(url))

		refresh = lxml.html.fromstring(response.text).cssselect('meta[http-equiv="refresh"]')

		if refresh:
			link = refresh[0].attrib['content'].partition("=")[2]
			return self._check_url(protocol, port, link)
		return True

	def _check_dpkg_installed_status(self):
		for package in self._packages():
			try:
				(expected, current) = self._dpkg_status(package)
				error = current != "installed"
			except subprocess.CalledProcessError:
				error = True
			if error:
				msg = "`dpkg -s {}` does not report as installed"
				return self._fail(msg.format(package))
		print("OK - dpkg reports correctly installed")
		return True

	def _check_dpkg_uninstalled_status(self):
		for package in self._packages():
			try:
				(expected, current) = self._dpkg_status(package)
				error = current not in ("not-installed", "unknown", "config-files")
			except subprocess.CalledProcessError as e:
				error = e.returncode != 1
			if error:
				msg = "`dpkg -s {}` does not report as uninstalled"
				return self._fail(msg.format(package))
		print("OK - dpkg reports correctly uninstalled")
		return True

	def _check_files_exist(self):
		for package in self._packages():
			output = subprocess.check_output(["dpkg", "--listfiles", package], text=True)
			for path in output.splitlines():
				if not os.path.exists(path):
					msg = "{} from {} does not exist in filesystem"
					return self._fail(msg.format(path, package))
		print("OK - All files exist in the filesystem after installation.")
		return True

	def _check_ucr_variables_exist(self):
		interface = self.info.get("web_interface")
		port_http = self.info.get("web_interface_port_http")
		port_https = self.info.get("web_interface_port_https")
		scheme = self.info.get("ucs_overview_category", "service")

		web_entries_base = "ucs/web/overview/entries/{}/{}".format(scheme, self.application)
		pairs = (
			("/link", interface), ("/port_http", str(port_http)),
			("/port_https", str(port_https))
		)

		if interface and port_http and port_https:
			unequal = [web_entries_base + ex for (ex, value) in pairs if self.ucr.get(web_entries_base + ex) != value]
			if unequal:
				msg = "following UCR variables not set correctly: {}"
				return self._fail(msg.format(", ".join(unequal)))

			msg = "OK - All UCR variables ({}) set correctly after installation."
			print(msg.format(web_entries_base))
		return True

	def _check_ucr_variables_dont_exist(self):
		repository = "repository/online/component/{}".format(self.info.get("component_id"))
		web_entries = "ucs/web/overview/entries/(admin|service)/{}".format(self.application)
		pattern = re.compile("{}|{}".format(repository, web_entries))
		active = [key for key in self.ucr.keys() if pattern.match(key)]
		if active:
			msg = "following UCR variables still active: {}"
			return self._fail(msg.format(", ".join(active)))
		print("OK - All UCR variables removed after uninstallation.")
		return True

	def _check_ldap_object_exists(self):
		try:
			utils.verify_ldap_object(self._get_dn())
		except utils.LDAPObjectNotFound as e:
			return self._fail("Not Found: " + str(e))
		print("OK - LDAP object created after installation.")
		return True

	def _check_ldap_object_doesnt_exist(self):
		try:
			utils.verify_ldap_object(self._get_dn(), should_exist=False)
		except utils.LDAPUnexpectedObjectFound as e:
			return self._fail("Found unexpected: " + str(e))
		print("OK - LDAP object removed after uninstallation.")
		return True

	def _check_url_accessible(self):
		interface = self.info.get("web_interface")
		port_http = self.info.get("web_interface_port_http")
		port_https = self.info.get("web_interface_port_https")

		if all((interface, port_http, port_https)) and \
			self._check_url("http", port_http, interface) and \
			self._check_url("https", port_https, interface):
			print("OK - Webinterface reachable after installation.")
		return True


class TestOperations(object):

	def __init__(self, app_center, application):
		self.app_center = app_center
		self.application = application

	def dry_run_successful(self, dry_run_result):
		print("Checking dry-run", dry_run_result)
		for host in dry_run_result:
			if dry_run_result[host]["errors"]:
				return False
			for app in dry_run_result[host]["packages"]:
				if dry_run_result[host]["packages"][app].get("broken"):
					return False
		return True

	def operation_successfull(self, result):
		print("Checking result", result)
		for host in result:
			for app in result[host]:
				if not result[host][app]["success"]:
					return False
		return True

	def operations_equal(self, expected, actual, msg=None):
		simple_equal = ("invokation_forbidden_details", "invokation_warning_details")
		set_equal = ("broken", "install", "remove")

		def compare_simple(key):
			return expected.get(key) == actual.get(key)

		def compare_set(key):
			return set(expected.get(key, [])) == set(actual.get(key, []))

		result = all(compare_simple(key) for key in simple_equal) and all(compare_set(key) for key in set_equal)
		if msg and not result:
			raise AppCenterCheckError(msg.format(self.application))
		return result

	def test_install(self, test_installed=True):
		dry_run = self.app_center.install_dry_run([self.application])
		if not self.dry_run_successful(dry_run):
			raise AppCenterCheckError("Dry-install of {} failed.".format(self.application))

		install = self.app_center.install([self.application])
		if not self.operation_successfull(install):
			raise AppCenterCheckError("install of {} failed.".format(self.application))

		post_installed_info = self.app_center.get(self.application)
		if test_installed:
			self.app_center.is_installed(self.application, info=post_installed_info, msg="{} is not installed")

			if not CheckOperations.installed(self.application, post_installed_info):
				msg = "{} is not installed correctly."
				raise AppCenterCheckError(msg.format(self.application))

	@contextlib.contextmanager
	def test_install_safe(self, test_installed=True):
		try:
			self.test_install(test_installed=test_installed)
			yield
		finally:
			if self.app_center.is_installed(self.application):
				self.app_center.remove([self.application])

	def test_upgrade(self, test_installed=True):
		# FIXME: This is needed to find the upgrade (updates the AppCenters caches)
		self.app_center.query()

		dry_run = self.app_center.upgrade_dry_run([self.application])
		if not self.dry_run_successful(dry_run):
			raise AppCenterCheckError("Dry-upgrade of {} failed.".format(self.application))

		upgrade = self.app_center.upgrade([self.application])
		if not self.operation_successfull(upgrade):
			raise AppCenterCheckError("upgrade of {} failed.".format(self.application))

		post_upgraded_info = self.app_center.get(self.application)
		if test_installed:
			self.app_center.is_installed(self.application, info=post_upgraded_info, msg="{} is not installed")

			if not CheckOperations.installed(self.application, post_upgraded_info):
				msg = "{} is not upgraded correctly."
				raise AppCenterCheckError(msg.format(self.application))

	def test_remove(self, test_uninstalled=True):
		dry_run = self.app_center.remove_dry_run([self.application])
		if not self.dry_run_successful(dry_run):
			raise AppCenterCheckError("Dry-remove of {} failed.".format(self.application))

		remove = self.app_center.remove([self.application])
		if not self.operation_successfull(remove):
			raise AppCenterCheckError("remove of {} failed.".format(self.application))

		post_uninstalled_info = self.app_center.get(self.application)
		if test_uninstalled:
			if self.app_center.is_installed(self.application, info=post_uninstalled_info):
				msg = "{} is still installed"
				raise AppCenterCheckError(msg.format(self.application))

			if not CheckOperations.uninstalled(self.application, post_uninstalled_info):
				msg = "{} is not uninstalled correctly."
				raise AppCenterCheckError(msg.format(self.application))

	def test_install_remove_cycle(self):
		info = self.app_center.get(self.application)
		if self.app_center.is_docker(self.application, info=info):
			msg = "{} is a docker application - skipping tests.."
			print(msg.format(self.application))
			return

		if self.app_center.is_installed(self.application, info=info):
			msg = "{} already installed"
			raise AppCenterCheckError(msg.format(self.application))

		with self.test_install_safe():
			self.test_remove()


@contextlib.contextmanager
def local_appcenter():
	restart_umc()
	setup_local_appcenter = get_action("dev-setup-local-appcenter")
	ucs_versions = AppCenterCache().get_ucs_versions()
	print("Setting up local app-center for UCS versions = %r." % (ucs_versions,))
	for ucs_version in ucs_versions:
		setup_local_appcenter.call(ucs_version=ucs_version)
	try:
		yield
	finally:
		print("Reverting local app-center.")
		setup_local_appcenter.call(revert=True)
		restart_umc()


def test_case(function):
	@functools.wraps(function)
	def wrapper(*args, **kwargs):
		print("Running {}{}".format(function.__name__, function.__doc__))
		app_center = AppCenterOperations()
		try:
			function(app_center, function.__name__.replace("_", "-"))
		except Exception:
			print("Error in {}{}".format(function.__name__, function.__doc__))
			raise
		print("Ok - {}{}".format(function.__name__, function.__doc__))
	return wrapper


def fail(message):
	raise AppCenterTestFailure(message)


if __name__ == "__main__":
	app_logger.log_to_stream()
	app_logger.get_base_logger().setLevel(logging.WARNING)

	with local_appcenter():
		app_center = AppCenterOperations()

		package = AppPackage.with_package(name="my-test-app", app_version="1.0")
		package.build_and_publish()

		test = TestOperations(app_center, package.app_id)
		test.test_install_remove_cycle()

		with test.test_install_safe():

			dependency = DebianPackage("my-dependency")
			dependency.build()

			upgrade = AppPackage.with_package(name=package.app_id, app_version="2.0", app_code=package.app_code, depends=[dependency])
			upgrade.build_and_publish()
			upgrade.remove_tempdir()
			dependency.remove()

			test.test_upgrade()
			test.test_uninstall()
