#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: software management
#
# Copyright 2011-2015 Univention GmbH
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

# standard library
import os
import locale
import time
import sys
#import urllib2
from httplib import HTTPException
from functools import wraps
import logging
from tempfile import NamedTemporaryFile

# related third party
import notifier
import notifier.threads
import apt # for independent apt.Cache

# univention
from univention.lib.package_manager import PackageManager, LockError
from univention.lib.umc_connection import UMCConnection
from univention.management.console.log import MODULE
from univention.management.console.modules.decorators import simple_response, sanitize, sanitize_list, multi_response
from univention.management.console.modules.sanitizers import PatternSanitizer, MappingSanitizer, DictSanitizer, StringSanitizer, ChoicesSanitizer, ListSanitizer, BooleanSanitizer
from univention.updater import UniventionUpdater
from univention.updater.errors import ConfigurationError
import univention.config_registry
import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.appcenter import get_action, AppManager
from univention.appcenter.utils import docker_is_running, call_process
from univention.appcenter.log import get_base_logger, log_to_logfile

# local application
from app_center import Application, AppcenterServerContactFailed, LICENSE
from sanitizers import basic_components_sanitizer, advanced_components_sanitizer, add_components_sanitizer
import constants
import util

_ = umc.Translation('univention-management-console-module-appcenter').translate


class NoneCandidate(object):
	''' Mock object if package has no candidate
	(may happen without network connection)
	'''
	def __init__(self):
		self.summary = self.version = self.description = self.priority = self.section = _('Package not found in repository')
		self.installed_size = 0

class ProgressInfoHandler(logging.Handler):
	def __init__(self, package_manager):
		super(ProgressInfoHandler, self).__init__()
		self.state = package_manager.progress_state

	def emit(self, record):
		if record.levelno >= logging.ERROR:
			self.state.error(record.msg)
		else:
			self.state.info(record.msg)


class ProgressPercentageHandler(ProgressInfoHandler):
	def emit(self, record):
		percentage = float(record.msg)
		self.state.percentage(percentage)
		self.state._finished = percentage >= 100

def error_handler(func):  # imported in apps module ;)
	@wraps(func)
	def _decorated(self, request, *a, **kwargs):
		try:
			return func(self, request, *a, **kwargs)
#		except (urllib2.HTTPError, urllib2.URLError) as exc:
#			raise umcm.UMC_Error(util.verbose_http_error(exc))
		except (SystemError, AppcenterServerContactFailed) as exc:
			MODULE.error(str(exc))
			raise umcm.UMC_Error(str(exc), status=500)
	return _decorated


class Instance(umcm.Base):

	def init(self):
		self.ucr = univention.config_registry.ConfigRegistry()
		self.ucr.load()

		util.install_opener(self.ucr)

		try:
			self.package_manager = PackageManager(
				info_handler=MODULE.process,
				step_handler=None,
				error_handler=MODULE.warn,
				lock=False,
			)
		except SystemError as exc:
			MODULE.error(str(exc))
			raise umcm.UMC_Error(str(exc), status=500)
		self.package_manager.set_finished() # currently not working. accepting new tasks
		self.uu = UniventionUpdater(False)
		self.component_manager = util.ComponentManager(self.ucr, self.uu)

		# in order to set the correct locale for Application
		locale.setlocale(locale.LC_ALL, str(self.locale))

		try:
			log_to_logfile()
		except IOError:
			pass

		# connect univention.appcenter.log to the progress-method
		handler = ProgressInfoHandler(self.package_manager)
		handler.setLevel(logging.INFO)
		get_base_logger().addHandler(handler)

		percentage = ProgressPercentageHandler(self.package_manager)
		percentage.setLevel(logging.DEBUG)
		get_base_logger().getChild('actions.install.progress').addHandler(percentage)
		get_base_logger().getChild('actions.upgrade.progress').addHandler(percentage)
		get_base_logger().getChild('actions.remove.progress').addHandler(percentage)

	@error_handler
	@simple_response
	def version(self):
		return Application.get_appcenter_version()

	@error_handler
	@simple_response
	def query(self):
		applications = Application.all(force_reread=True)
		if not docker_is_running():
			MODULE.warn('Docker is not running! Trying to start it now...')
			call_process(['invoke-rc.d', 'docker', 'start'])
			if not docker_is_running():
				raise umcm.UMC_CommandError(_('The docker service is not running! The App Center will not work properly. Make sure docker.io is installed, try starting the service with "invoke-rc.d docker start"'))
		result = []
		self.package_manager.reopen_cache()
		hosts = util.get_all_hosts()
		domainwide_managed = Application.domainwide_managed(hosts)
		for application in applications:
			if application.should_show_up_in_app_center(self.package_manager, domainwide_managed=domainwide_managed):
				props = application.to_dict(self.package_manager, domainwide_managed, hosts)
				result.append(props)
		return result

	@error_handler
	@simple_response
	def sync_ldap(self, application=None):
		# TODO: Remove in (UCS 3.2) + 1
		self.ucr.load()
		for old, new in [('tine20org', 'tine20'),]:
			if util.component_registered(old, self.ucr):
				util.rename_app(old, new, self.component_manager, self.package_manager)
		self.ucr.load()

		if application is not None:
			applications = [Application.find(application)]
		else:
			applications = Application.all()
		for application in applications:
			if application is None:
				continue
			application.tell_ldap(self.ucr, self.package_manager, inform_about_error=False)

	# used in updater-umc
	@error_handler
	@simple_response
	def get_by_component_id(self, component_id):
		all_apps = Application.all(force_reread=True)
		def _get_by_component_id(component, apps):
			for app in apps:
				for version in app.versions:
					if version.component_id == component:
						return version
		if isinstance(component_id, list):
			requested_apps = []
			for cid in component_id:
				version = _get_by_component_id(cid, all_apps)
				if version:
					requested_apps.append(version.to_dict(self.package_manager))
				else:
					requested_apps.append(None)
			return requested_apps
		else:
			version = _get_by_component_id(component_id, all_apps)
			if version:
				return version.to_dict(self.package_manager)
			else:
				raise umcm.UMC_CommandError(_('Could not find an application for %s') % component_id)

	# used in updater-umc
	@error_handler
	@simple_response
	def app_updates(self):
		self.package_manager.reopen_cache()
		applications = Application.all_installed(self.package_manager, force_reread=True)
		hosts = util.get_all_hosts()
		domainwide_managed = Application.domainwide_managed(hosts)
		return [app.to_dict(self.package_manager, domainwide_managed, hosts) for app in applications if app.candidate is not None]

	@error_handler
	@sanitize(application=StringSanitizer(minimum=1, required=True))
	@simple_response
	def get(self, application):
		application = Application.find(application)
		if application is None:
			raise umcm.UMC_CommandError(_('Could not find an application for %s') % (application,))
		self.package_manager.reopen_cache()
		return application.to_dict(self.package_manager)

	@sanitize(application=StringSanitizer(minimum=1, required=True), values=DictSanitizer({}))
	@simple_response
	def configure(self, application, autostart, values):
		application = AppManager.find(application)
		configure = get_action('configure')
		configure.call(app=application, set_vars=values, autostart=autostart)

	@sanitize(application=StringSanitizer(minimum=1, required=True), mode=ChoicesSanitizer(['start', 'stop']))
	@simple_response
	def app_service(self, application, mode):
		application = AppManager.find(application)
		service = get_action(mode)
		service.call(app=application)

	def _invoke_docker(self, function, application, force, values):
		can_continue = force # always show configuration after first request
		serious_problems = False
		app = application.to_app()
		errors, warnings = app.check(function)
		if errors:
			MODULE.process('Cannot %s %s: %r' % (function, application.id, errors))
			serious_problems = True
			can_continue = False
		if warnings:
			MODULE.process('Warning trying to %s %s: %r' % (function, application.id, warnings))
		result = {
			'serious_problems': serious_problems,
			'invokation_forbidden_details': errors,
			'invokation_warning_details': warnings,
			'can_continue': can_continue,
			'software_changes_computed': False,
		}
		if can_continue:
			def _thread(app, function):
				with self.package_manager.locked(reset_status=True, set_finished=True):
					with self.package_manager.no_umc_restart(exclude_apache=True):
						if function not in ['install', 'uninstall', 'upgrade']:
							raise umcm.UMC_CommandError('Cannot %s. Not supported!' % function)
						if function == 'uninstall':
							function = 'remove'
						action = get_action(function)
						kwargs = {'noninteractive': True}
						if function == 'install':
							kwargs['set_vars'] = values
						if function == 'uninstall':
							kwargs['keep_data'] = not values.get('dont_keep_data', False)
						with NamedTemporaryFile('w+b') as password_file:
							password_file.write(self._password)
							password_file.flush()
							action.call(app=app, username=self._username, pwdfile=password_file.name, **kwargs)
			def _finished(thread, result):
				if isinstance(result, BaseException):
					MODULE.warn('Exception during %s %s: %s' % (function, app.id, str(result)))
			thread = notifier.threads.Simple('invoke',
				notifier.Callback(_thread, app, function), _finished)
			thread.run()
		return result

	@error_handler
	def invoke_dry_run(self, request):
		request.options['only_dry_run'] = True
		self.invoke(request)

	@error_handler
	@sanitize(
		function=ChoicesSanitizer(['install', 'uninstall', 'update', 'install-schema', 'update-schema'], required=True),
		application=StringSanitizer(minimum=1, required=True),
		force=BooleanSanitizer(),
		host=StringSanitizer(),
		only_dry_run=BooleanSanitizer(),
		dont_remote_install=BooleanSanitizer(),
		values=DictSanitizer({})
	)
	def invoke(self, request):
		# ATTENTION!!!!!!!
		# this function has to stay compatible with the very first App Center installations (Dec 2012)
		# if you add new arguments that change the behaviour
		# you should add a new method (see invoke_dry_run) or add a function name (e.g. install-schema)
		# this is necessary because newer app center may talk remotely with older one
		#   that does not understand new arguments and behaves the old way (in case of
		#   dry_run: install application although they were asked to dry_run)
		host = request.options.get('host')
		function = request.options.get('function')
		send_as = function
		if function.startswith('install'):
			function = 'install'
		if function.startswith('update'):
			function = 'update'
		application_id = request.options.get('application')
		application = Application.find(application_id)
		if application is None:
			raise umcm.UMC_CommandError(_('Could not find an application for %s') % (application_id,))
		force = request.options.get('force')
		values = request.options.get('values')
		only_dry_run = request.options.get('only_dry_run')
		dont_remote_install = request.options.get('dont_remote_install')
		only_master_packages = send_as.endswith('schema')
		MODULE.process('Try to %s (%s) %s on %s. Force? %r. Only master packages? %r. Prevent installation on other systems? %r. Only dry run? %r.' % (function, send_as, application_id, host, force, only_master_packages, dont_remote_install, only_dry_run))

		# REMOTE invocation!
		if host and host != self.ucr.get('hostname'):
			try:
				connection = UMCConnection(host, error_handler=MODULE.warn)
				connection.auth(self._username, self._password)
				result = connection.request('appcenter/invoke', request.options)
			except HTTPException:
				result = {
					'unreachable' : [host],
					'master_unreachable' : True,
					'serious_problems' : True,
					'software_changes_computed' : True, # not really...
				}
			else:
				if result['can_continue']:
					def _thread_remote(_connection, _package_manager):
						with _package_manager.locked(reset_status=True, set_finished=True):
							_package_manager.unlock() # not really locked locally, but busy, so "with locked()" is appropriate
							Application._query_remote_progress(_connection, _package_manager)
					def _finished_remote(thread, result):
						if isinstance(result, BaseException):
							MODULE.warn('Exception during %s %s: %s' % (function, application_id, str(result)))
					thread = notifier.threads.Simple('invoke',
						notifier.Callback(_thread_remote, connection, self.package_manager), _finished_remote)
					thread.run()
			self.finished(request.id, result)
			return

		# DOCKER is different!
		# TODO
		if application and application.get('docker'):
			result = self._invoke_docker(function, application, force, values)
			self.finished(request.id, result)
			return

		# make sure that the application can be installed/updated
		can_continue = True
		delayed_can_continue = True
		serious_problems = False
		result = {
			'install' : [],
			'remove' : [],
			'broken' : [],
			'unreachable' : [],
			'master_unreachable' : False,
			'serious_problems' : False,
			'hosts_info' : {},
			'problems_with_hosts' : False,
			'serious_problems_with_hosts' : False,
			'invokation_forbidden_details' : {},
			'invokation_warning_details' : {},
			'software_changes_computed' : False,
		}
		if not application:
			MODULE.process('Application not found: %s' % application_id)
			can_continue = False
		if can_continue and not only_master_packages:
			forbidden, warnings = application.check_invokation(function, self.package_manager)
			if forbidden:
				MODULE.process('Cannot %s %s: %r' % (function, application_id, forbidden))
				result['invokation_forbidden_details'] = forbidden
				can_continue = False
				serious_problems = True
			if warnings:
				MODULE.process('Warning trying to %s %s: %r' % (function, application_id, forbidden))
				result['invokation_warning_details'] = warnings
				if not force:
					# dont stop "immediately".
					#   compute the package changes!
					delayed_can_continue = False
		result['serious_problems'] = serious_problems
		result['can_continue'] = can_continue
		try:
			if can_continue:
				if self._working():
					# make it multi-tab safe (same session many buttons to be clicked)
					raise LockError()
				with self.package_manager.locked(reset_status=True):
					previously_registered_by_dry_run = False
					if can_continue and function in ('install', 'update'):
						remove_component = only_dry_run
						dry_run_result, previously_registered_by_dry_run = application.install_dry_run(self.package_manager, self.component_manager, remove_component=remove_component, username=self._username, password=self._password, only_master_packages=only_master_packages, dont_remote_install=dont_remote_install, function=function, force=force)
						result.update(dry_run_result)
						result['software_changes_computed'] = True
						serious_problems = bool(result['broken'] or result['master_unreachable'] or result['serious_problems_with_hosts'])
						if serious_problems or (not force and (result['unreachable'] or result['install'] or result['remove'] or result['problems_with_hosts'])):
							MODULE.process('Problems encountered or confirmation required. Removing component %s' % application.component_id)
							if not remove_component:
								# component was not removed automatically after dry_run
								if application.candidate:
									# operation on candidate failed. re-register original application
									application.register(self.component_manager, self.package_manager)
								else:
									# operation on self failed. unregister all
									application.unregister_all_and_register(None, self.component_manager, self.package_manager)
							can_continue = False
					elif can_continue and function in ('uninstall',) and not force:
						result['remove'] = application.uninstall_dry_run(self.package_manager)
						result['software_changes_computed'] = True
						can_continue = False
					can_continue = can_continue and delayed_can_continue
					result['serious_problems'] = serious_problems
					result['can_continue'] = can_continue

					if can_continue and not only_dry_run:
						def _thread(module, application, function):
							with module.package_manager.locked(set_finished=True):
								with module.package_manager.no_umc_restart(exclude_apache=True):
									if function in ('install', 'update'):
										# dont have to add component: already added during dry_run
										return application.install(module.package_manager, module.component_manager, add_component=only_master_packages, send_as=send_as, username=self._username, password=self._password, only_master_packages=only_master_packages, dont_remote_install=dont_remote_install, previously_registered_by_dry_run=previously_registered_by_dry_run)
									else:
										return application.uninstall(module.package_manager, module.component_manager, self._username, self._password)
						def _finished(thread, result):
							if isinstance(result, BaseException):
								MODULE.warn('Exception during %s %s: %s' % (function, application_id, str(result)))
						thread = notifier.threads.Simple('invoke',
							notifier.Callback(_thread, self, application, function), _finished)
						thread.run()
					else:
						self.package_manager.set_finished() # nothing to do, ready to take new commands
			self.finished(request.id, result)
		except LockError:
			# make it thread safe: another process started a package manager
			# this module instance already has a running package manager
			raise umcm.UMC_CommandError(_('Another package operation is in progress'))

	def keep_alive(self, request):
		''' Fix for Bug #30611: UMC kills appcenter module
		if no request is sent for $(ucr get umc/module/timeout).
		this happens if a user logs out during a very long installation.
		this function will be run by the frontend to always have one connection open
		to prevent killing the module. '''
		def _thread():
			while not self.package_manager.progress_state._finished:
				time.sleep(1)
		def _finished(thread, result):
			success = not isinstance(result, BaseException)
			if not success:
				MODULE.warn('Exception during keep_alive: %s' % result)
			self.finished(request.id, success)
		thread = notifier.threads.Simple('keep_alive',
			notifier.Callback(_thread), _finished)
		thread.run()

	@simple_response
	def ping(self):
		return True

	@error_handler
	@simple_response
	def buy(self, application):
		application = Application.find(application)
		if not application or not application.get('useshop'):
			return None
		ret = {}
		ret['key_id'] = LICENSE.uuid
		ret['ucs_version'] = self.ucr.get('version/version')
		ret['app_id'] = application.id
		ret['app_version'] = application.version
		# ret['locale'] = locale.getlocale()[0] # done by frontend
		ret['user_count'] = None # FIXME: get users and computers from license
		ret['computer_count'] = None
		return ret

	@error_handler
	@simple_response
	def enable_disable_app(self, application, enable=True):
		application = Application.find(application)
		if not application:
			return
		should_update = False
		if enable:
			should_update = application.enable_component(self.component_manager)
		else:
			should_update = application.disable_component(self.component_manager)
		if should_update:
			self.package_manager.update()

	@error_handler
	@simple_response
	def packages_sections(self):
		""" fills the 'sections' combobox in the search form """

		sections = set()
		cache = apt.Cache()
		for package in cache:
			sections.add(package.section)

		return sorted(sections)

	@error_handler
	@sanitize(pattern=PatternSanitizer(required=True))
	@simple_response
	def packages_query(self, pattern, section='all', key='package'):
		""" Query to fill the grid. Structure is fixed here. """
		result = []
		for package in self.package_manager.packages(reopen=True):
			if section == 'all' or package.section == section:
				toshow = False
				if pattern.pattern == '^.*$':
					toshow = True
				elif key == 'package' and pattern.search(package.name):
					toshow = True
				elif key == 'description' and package.candidate and pattern.search(package.candidate.raw_description):
					toshow = True
				if toshow:
					result.append(self._package_to_dict(package, full=False))
		return result

	@error_handler
	@simple_response
	def packages_get(self, package):
		""" retrieves full properties of one package """

		package = self.package_manager.get_package(package)
		if package is not None:
			return self._package_to_dict(package, full=True)
		else:
			# TODO: 404?
			return {}

	@error_handler
	@sanitize(function=MappingSanitizer({
				'install' : 'install',
				'upgrade' : 'install',
				'uninstall' : 'remove',
			}, required=True),
		packages=ListSanitizer(StringSanitizer(minimum=1), required=True),
		update=BooleanSanitizer()
		)
	@simple_response
	def packages_invoke_dry_run(self, packages, function, update):
		if update:
			self.package_manager.update()
		packages = self.package_manager.get_packages(packages)
		kwargs = {'install' : [], 'remove' : [], 'dry_run' : True}
		if function == 'install':
			kwargs['install'] = packages
		else:
			kwargs['remove'] = packages
		return dict(zip(['install', 'remove', 'broken'], self.package_manager.mark(**kwargs)))

	@error_handler
	@sanitize(function=MappingSanitizer({
				'install' : 'install',
				'upgrade' : 'install',
				'uninstall' : 'remove',
			}, required=True),
		packages=ListSanitizer(StringSanitizer(minimum=1), required=True)
		)
	def packages_invoke(self, request):
		""" executes an installer action """
		packages = request.options.get('packages')
		function = request.options.get('function')

		try:
			if self._working():
				# make it multi-tab safe (same session many buttons to be clicked)
				raise LockError()
			with self.package_manager.locked(reset_status=True):
				not_found = [pkg_name for pkg_name in packages if self.package_manager.get_package(pkg_name) is None]
				self.finished(request.id, {'not_found' : not_found})

				if not not_found:
					def _thread(package_manager, function, packages):
						with package_manager.locked(set_finished=True):
							with package_manager.no_umc_restart(exclude_apache=True):
								if function == 'install':
									package_manager.install(*packages)
								else:
									package_manager.uninstall(*packages)
					def _finished(thread, result):
						if isinstance(result, BaseException):
							MODULE.warn('Exception during %s %s: %r' % (function, packages, str(result)))
					thread = notifier.threads.Simple('invoke',
						notifier.Callback(_thread, self.package_manager, function, packages), _finished)
					thread.run()
				else:
					self.package_manager.set_finished() # nothing to do, ready to take new commands
		except LockError:
			# make it thread safe: another process started a package manager
			# this module instance already has a running package manager
			raise umcm.UMC_CommandError(_('Another package operation is in progress'))

	def _working(self):
		return not self.package_manager.progress_state._finished

	@error_handler
	@simple_response
	def working(self):
		# TODO: PackageManager needs is_idle() or something
		#   preferably the package_manager can tell what is currently executed:
		#   package_manager.is_working() => False or _('Installing UCC')
		return self._working()

	@error_handler
	@simple_response
	def progress(self):
		timeout = 5
		return self.package_manager.poll(timeout)

	def _package_to_dict(self, package, full):
		""" Helper that extracts properties from a 'apt_pkg.Package' object
			and stores them into a dictionary. Depending on the 'full'
			switch, stores only limited (for grid display) or full
			(for detail view) set of properties.
		"""
		installed = package.installed # may be None
		found = True
		candidate = package.candidate
		found = candidate is not None
		if not found:
			candidate = NoneCandidate()

		result = {
			'package': package.name,
			'installed': package.is_installed,
			'upgradable': package.is_upgradable and found,
			'summary': candidate.summary,
		}

		# add (and translate) a combined status field
		# *** NOTE *** we translate it here: if we would use the Custom Formatter
		#		of the grid then clicking on the sort header would not work.
		if package.is_installed:
			if package.is_upgradable:
				result['status'] = _('upgradable')
			else:
				result['status'] = _('installed')
		else:
			result['status'] = _('not installed')

		# additional fields needed for detail view
		if full:
			# Some fields differ depending on whether the package is installed or not:
			if package.is_installed:
				result['section'] = installed.section
				result['priority'] = installed.priority or ''
				result['summary'] = installed.summary # take the current one
				result['description'] = installed.description
				result['installed_version'] = installed.version
				result['size'] = installed.installed_size
				if package.is_upgradable:
					result['candidate_version'] = candidate.version
			else:
				del result['upgradable'] # not installed: don't show 'upgradable' at all
				result['section'] = candidate.section
				result['priority'] = candidate.priority or ''
				result['description'] = candidate.description
				result['size'] = candidate.installed_size
				result['candidate_version'] = candidate.version
			# format size to handle bytes
			size = result['size']
			byte_mods = ['B', 'kB', 'MB']
			for byte_mod in byte_mods:
				if size < 10000:
					break
				size = float(size) / 1000 # MB, not MiB
			else:
				size = size * 1000 # once too often
			if size == int(size):
				format_string = '%d %s'
			else:
				format_string = '%.2f %s'
			result['size'] = format_string % (size, byte_mod)

		return result

	@error_handler
	@simple_response
	def components_query(self):
		"""	Returns components list for the grid in the ComponentsPage.
		"""
		# be as current as possible.
		self.uu.ucr_reinit()
		self.ucr.load()

		result = []
		for comp in self.uu.get_all_components():
			result.append(self.component_manager.component(comp))
		return result

	@error_handler
	@sanitize_list(StringSanitizer())
	@multi_response(single_values=True)
	def components_get(self, iterator, component_id):
		# be as current as possible.
		self.uu.ucr_reinit()
		self.ucr.load()
		for component_id in iterator:
			yield self.component_manager.component(component_id)

	@error_handler
	@sanitize_list(DictSanitizer({'object' : advanced_components_sanitizer}))
	@multi_response
	def components_put(self, iterator, object):
		"""Writes back one or more component definitions.
		"""
		# umc.widgets.Form wraps the real data into an array:
		#
		#	[
		#		{
		#			'object' : { ... a dict with the real data .. },
		#			'options': None
		#		},
		#		... more such entries ...
		#	]
		#
		# Current approach is to return a similarly structured array,
		# filled with elements, each one corresponding to one array
		# element of the request:
		#
		#	[
		#		{
		#			'status'	:	a number where 0 stands for success, anything else
		#							is an error code
		#			'message'	:	a result message
		#			'object'	:	a dict of field -> error message mapping, allows
		#							the form to show detailed error information
		#		},
		#		... more such entries ...
		#	]
		with util.set_save_commit_load(self.ucr) as super_ucr:
			for object, in iterator:
				yield self.component_manager.put(object, super_ucr)
		self.package_manager.update()

	# do the same as components_put (update)
	# but dont allow adding an already existing entry
	components_add = sanitize_list(DictSanitizer({'object' : add_components_sanitizer}))(components_put)
	components_add.__name__ = 'components_add'

	@error_handler
	@sanitize_list(StringSanitizer())
	@multi_response(single_values=True)
	def components_del(self, iterator, component_id):
		for component_id in iterator:
			yield self.component_manager.remove(component_id)
		self.package_manager.update()

	@error_handler
	@multi_response
	def settings_get(self, iterator):
		# *** IMPORTANT *** Our UCR copy must always be current. This is not only
		#	to catch up changes made via other channels (ucr command line etc),
		#	but also to reflect the changes we have made ourselves!
		self.ucr.load()

		for _ in iterator:
			yield {
				'unmaintained' : self.ucr.is_true('repository/online/unmaintained', False),
				'server' : self.ucr.get('repository/online/server', ''),
				'prefix' : self.ucr.get('repository/online/prefix', ''),
			}

	@error_handler
	@sanitize_list(DictSanitizer({'object' : basic_components_sanitizer}),
		min_elements=1, max_elements=1 # moduleStore with one element...
	)
	@multi_response
	def settings_put(self, iterator, object):
		# FIXME: returns values although it should yield (multi_response)
		changed = False
		# Set values into our UCR copy.
		try:
			with util.set_save_commit_load(self.ucr) as super_ucr:
				for object, in iterator:
					for key, value in object.iteritems():
						MODULE.info("   ++ Setting new value for '%s' to '%s'" % (key, value))
						super_ucr.set_registry_var('%s/%s' % (constants.ONLINE_BASE, key), value)
				changed = super_ucr.changed()
		except Exception as e:
			MODULE.warn("   !! Writing UCR failed: %s" % str(e))
			return [{'message' : str(e), 'status' : constants.PUT_WRITE_ERROR}]

		self.package_manager.update()

		# Bug #24878: emit a warning if repository is not reachable
		try:
			updater = self.uu
			for line in updater.print_version_repositories().split('\n'):
				if line.strip():
					break
			else:
				raise ConfigurationError()
		except ConfigurationError:
			msg = _("There is no repository at this server (or at least none for the current UCS version)")
			MODULE.warn("   !! Updater error: %s" % msg)
			response = {'message' : msg, 'status' : constants.PUT_UPDATER_ERROR}
			# if nothing was committed, we want a different type of error code,
			# just to appropriately inform the user
			if changed:
				response['status'] = constants.PUT_UPDATER_NOREPOS
			return [response]
		except:
			info = sys.exc_info()
			emsg = '%s: %s' % info[:2]
			MODULE.warn("   !! Updater error [%s]: %s" % (emsg))
			return [{'message' : str(info[1]), 'status' : constants.PUT_UPDATER_ERROR}]
		return [{'status' : constants.PUT_SUCCESS}]

