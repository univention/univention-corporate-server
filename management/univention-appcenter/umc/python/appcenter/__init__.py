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
from contextlib import contextmanager
#import urllib2
from httplib import HTTPException
import logging
from tempfile import NamedTemporaryFile

# related third party
import notifier
import notifier.threads
import apt  # for independent apt.Cache

# univention
from univention.lib.package_manager import PackageManager, LockError
from univention.lib.umc_connection import UMCConnection
from univention.management.console.log import MODULE
from univention.management.console.modules.decorators import simple_response, sanitize, sanitize_list, multi_response, require_password
from univention.management.console.modules.mixins import ProgressMixin
from univention.management.console.modules.sanitizers import PatternSanitizer, MappingSanitizer, DictSanitizer, StringSanitizer, ChoicesSanitizer, ListSanitizer, BooleanSanitizer
from univention.updater.tools import UniventionUpdater
from univention.updater.errors import ConfigurationError
import univention.config_registry
import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.appcenter import get_action, AppManager
from univention.appcenter.utils import docker_is_running, call_process
from univention.appcenter.log import get_base_logger, log_to_logfile

# local application
from app_center import Application, AppcenterServerContactFailed, LICENSE
from sanitizers import AppSanitizer, basic_components_sanitizer, advanced_components_sanitizer, add_components_sanitizer
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


class UMCProgressHandler(logging.Handler):
	def __init__(self, progress):
		super(UMCProgressHandler, self).__init__()
		self.progress = progress

	def emit(self, record):
		msg = record.msg
		if isinstance(record.msg, Exception):
			msg = str(msg)
		detail = {'level': record.levelname, 'message': msg}
		self.progress.progress(detail=detail, message=msg)


class ProgressInfoHandler(logging.Handler):
	def __init__(self, package_manager):
		super(ProgressInfoHandler, self).__init__()
		self.state = package_manager.progress_state

	def emit(self, record):
		msg = record.msg
		if isinstance(record.msg, Exception):
			msg = str(msg)
		if record.levelno >= logging.ERROR:
			self.state.error(msg)
		else:
			self.state.info(msg)


class ProgressPercentageHandler(ProgressInfoHandler):
	def emit(self, record):
		percentage = float(record.msg)
		self.state.percentage(percentage)
		self.state._finished = percentage >= 100


class Instance(umcm.Base, ProgressMixin):

	def init(self):
		os.umask(0022)  # umc umask is too restrictive for app center as it creates a lot of files in docker containers
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
		self.package_manager.set_finished()  # currently not working. accepting new tasks
		self.uu = UniventionUpdater(False)
		self.component_manager = util.ComponentManager(self.ucr, self.uu)
		AppManager.set_package_manager(self.package_manager)

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

	def error_handling(self, exc, etype, etraceback):
		if isinstance(exc, (SystemError, AppcenterServerContactFailed)):
			MODULE.error(str(exc))
			raise umcm.UMC_Error(str(exc), status=500)

	@simple_response
	def version(self):
		info = get_action('info')
		return info.get_compatibility()

	@simple_response
	def query(self):
		if self.ucr.is_true('appcenter/umc/update/always', True):
			update = get_action('update')
			update.call()
			Application.all(force_reread=True, only_local=True)
		Application.all(only_local=True)  # cache 'em!
		list_apps = get_action('list')
		domain = get_action('domain')
		apps = list_apps.get_apps()
		self.ucr.load()
		if not self.ucr.get('docker/container/uuid'):
			if not docker_is_running():
				MODULE.warn('Docker is not running! Trying to start it now...')
				call_process(['invoke-rc.d', 'docker', 'start'])
				if not docker_is_running():
					raise umcm.UMC_CommandError(_('The docker service is not running! The App Center will not work properly. Make sure docker.io is installed, try starting the service with "service docker start"'))
		return domain.to_dict(apps)

	@simple_response
	def sync_ldap(self):
		register = get_action('register')
		register.call(register_task=['app'])

	# used in updater-umc
	@simple_response
	def get_by_component_id(self, component_id):
		domain = get_action('domain')
		if isinstance(component_id, list):
			requested_apps = [AppManager.find_by_component_id(component_id) for cid in component_id]
			return domain.to_dict(requested_apps)
		else:
			app = AppManager.find_by_component_id(component_id)
			if app:
				return domain.to_dict([app])[0]
			else:
				raise umcm.UMC_CommandError(_('Could not find an application for %s') % component_id)

	# used in updater-umc
	@simple_response
	def app_updates(self):
		upgrade = get_action('upgrade')
		domain = get_action('domain')
		return domain.to_dict(list(upgrade.iter_upgradable_apps()))

	@sanitize(application=StringSanitizer(minimum=1, required=True))
	@simple_response
	def get(self, application):
		domain = get_action('domain')
		app = AppManager.find(application)
		if app is None:
			raise umcm.UMC_CommandError(_('Could not find an application for %s') % (application,))
		return domain.to_dict([app])[0]

	@sanitize(app=AppSanitizer(required=True), values=DictSanitizer({}))
	@simple_response
	def configure(self, app, autostart, values):
		configure = get_action('configure')
		configure.call(app=app, set_vars=values, autostart=autostart)

	@sanitize(app=AppSanitizer(required=True), mode=ChoicesSanitizer(['start', 'stop']))
	@simple_response
	def app_service(self, app, mode):
		service = get_action(mode)
		service.call(app=app)

	@require_password
	def _invoke_docker(self, function, application, force, values):
		can_continue = force  # always show configuration after first request
		serious_problems = False
		app = AppManager.find(application.id)
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
						if function not in ['install', 'uninstall', 'update']:
							raise umcm.UMC_CommandError('Cannot %s. Not supported!' % function)
						if function == 'update':
							function = 'upgrade'
						if function == 'uninstall':
							function = 'remove'
						action = get_action(function)
						kwargs = {'noninteractive': True}
						if function == 'install':
							kwargs['set_vars'] = values
						if function == 'uninstall':
							kwargs['keep_data'] = not values.get('dont_keep_data', False)
						with NamedTemporaryFile('w+b') as password_file:
							password_file.write(self.password)
							password_file.flush()
							action.call(app=app, username=self._username, pwdfile=password_file.name, **kwargs)

			def _finished(thread, result):
				if isinstance(result, BaseException):
					MODULE.warn('Exception during %s %s: %s' % (function, app.id, str(result)))
				self.package_manager._hacked_thread_result = (result, thread)
			thread = notifier.threads.Simple('invoke',
				notifier.Callback(_thread, app, function), _finished)
			thread.run()
		return result

	def invoke_dry_run(self, request):
		request.options['only_dry_run'] = True
		self.invoke(request)

	@require_password
	@sanitize(
			function=MappingSanitizer({
				'install': 'install',
				'update': 'upgrade',
				'uninstall': 'remove',
			}, required=True),
			app=AppSanitizer(required=True),
			force=BooleanSanitizer(),
			values=DictSanitizer({})
	)
	@simple_response(with_progress=True)
	def invoke_docker(self, function, app, force, values, progress):
		with self.locked():
			serious_problems = False
			progress.title = _('%s: Running tests') % (app.name,)
			errors, warnings = app.check(function)
			can_continue = force  # "dry_run"
			if errors:
				MODULE.process('Cannot %s %s: %r' % (function, app.id, errors))
				serious_problems = True
				can_continue = False
			if warnings:
				MODULE.process('Warning trying to %s %s: %r' % (function, app.id, warnings))
			result = {
				'serious_problems': serious_problems,
				'invokation_forbidden_details': errors,
				'invokation_warning_details': warnings,
				'can_continue': can_continue,
				'software_changes_computed': False,
			}
			if can_continue:
				kwargs = {'noninteractive': True}
				if function == 'install':
					progress.title = _('Installing %s') % (app.name,)
					kwargs['set_vars'] = values
				elif function == 'uninstall':
					progress.title = _('Uninstalling %s') % (app.name,)
				elif function == 'upgrade':
					progress.title = _('Upgrading %s') % (app.name,)
				action = get_action(function)
				handler = UMCProgressHandler(progress)
				handler.setLevel(logging.INFO)
				action.logger.addHandler(handler)
				try:
					result['success'] = action.call(app=app, username=self.username, password=self.password, **kwargs)
				finally:
					action.logger.removeHandler(handler)
			return result

	@contextmanager
	def locked(self):
		with self.package_manager.locked(reset_status=True, set_finished=True):
			yield

	@require_password
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
				connection.auth(self._username, self.password)
				result = connection.request('appcenter/invoke', request.options)
			except HTTPException:
				result = {
					'unreachable': [host],
					'master_unreachable': True,
					'serious_problems': True,
					'software_changes_computed': True,  # not really...
				}
			else:
				if result['can_continue']:
					def _thread_remote(_connection, _package_manager):
						with _package_manager.locked(reset_status=True, set_finished=True):
							_package_manager.unlock()   # not really locked locally, but busy, so "with locked()" is appropriate
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
			'install': [],
			'remove': [],
			'broken': [],
			'unreachable': [],
			'master_unreachable': False,
			'serious_problems': False,
			'hosts_info': {},
			'problems_with_hosts': False,
			'serious_problems_with_hosts': False,
			'invokation_forbidden_details': {},
			'invokation_warning_details': {},
			'software_changes_computed': False,
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
						dry_run_result, previously_registered_by_dry_run = application.install_dry_run(self.package_manager, self.component_manager, remove_component=remove_component, username=self._username, password=self.password, only_master_packages=only_master_packages, dont_remote_install=dont_remote_install, function=function, force=force)
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
										return application.install(module.package_manager, module.component_manager, add_component=only_master_packages, send_as=send_as, username=self._username, password=self.password, only_master_packages=only_master_packages, dont_remote_install=dont_remote_install, previously_registered_by_dry_run=previously_registered_by_dry_run)
									else:
										return application.uninstall(module.package_manager, module.component_manager, self._username, self.password)

						def _finished(thread, result):
							if isinstance(result, BaseException):
								MODULE.warn('Exception during %s %s: %s' % (function, application_id, str(result)))
						thread = notifier.threads.Simple('invoke',
							notifier.Callback(_thread, self, application, function), _finished)
						thread.run()
					else:
						self.package_manager.set_finished()  # nothing to do, ready to take new commands
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

	@simple_response
	def buy(self, application):
		app = AppManager.find(application)
		if not app or not app.shop_url:
			return None
		ret = {}
		ret['key_id'] = LICENSE.uuid
		ret['ucs_version'] = self.ucr.get('version/version')
		ret['app_id'] = app.id
		ret['app_version'] = app.version
		# ret['locale'] = locale.getlocale()[0] # done by frontend
		ret['user_count'] = None  # FIXME: get users and computers from license
		ret['computer_count'] = None
		return ret

	@simple_response
	def enable_disable_app(self, application, enable=True):
		app = AppManager.find(application)
		if not app:
			return
		stall = get_action('stall')
		stall.call(app=app, undo=enable)

	@simple_response
	def packages_sections(self):
		""" fills the 'sections' combobox in the search form """

		sections = set()
		cache = apt.Cache()
		for package in cache:
			sections.add(package.section)

		return sorted(sections)

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

	@simple_response
	def packages_get(self, package):
		""" retrieves full properties of one package """

		package = self.package_manager.get_package(package)
		if package is not None:
			return self._package_to_dict(package, full=True)
		else:
			# TODO: 404?
			return {}

	@sanitize(function=MappingSanitizer({
				'install': 'install',
				'upgrade': 'install',
				'uninstall': 'remove',
			}, required=True),
		packages=ListSanitizer(StringSanitizer(minimum=1), required=True),
		update=BooleanSanitizer()
		)
	@simple_response
	def packages_invoke_dry_run(self, packages, function, update):
		if update:
			self.package_manager.update()
		packages = self.package_manager.get_packages(packages)
		kwargs = {'install': [], 'remove': [], 'dry_run': True}
		if function == 'install':
			kwargs['install'] = packages
		else:
			kwargs['remove'] = packages
		return dict(zip(['install', 'remove', 'broken'], self.package_manager.mark(**kwargs)))

	@sanitize(function=MappingSanitizer({
				'install': 'install',
				'upgrade': 'install',
				'uninstall': 'remove',
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
				self.finished(request.id, {'not_found': not_found})

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
					self.package_manager.set_finished()  # nothing to do, ready to take new commands
		except LockError:
			# make it thread safe: another process started a package manager
			# this module instance already has a running package manager
			raise umcm.UMC_CommandError(_('Another package operation is in progress'))

	def _working(self):
		return not self.package_manager.progress_state._finished

	@simple_response
	def working(self):
		# TODO: PackageManager needs is_idle() or something
		#   preferably the package_manager can tell what is currently executed:
		#   package_manager.is_working() => False or _('Installing UCC')
		return self._working()

	@simple_response
	def custom_progress(self):
		timeout = 5
		return self.package_manager.poll(timeout)

	def _package_to_dict(self, package, full):
		""" Helper that extracts properties from a 'apt_pkg.Package' object
			and stores them into a dictionary. Depending on the 'full'
			switch, stores only limited (for grid display) or full
			(for detail view) set of properties.
		"""
		installed = package.installed  # may be None
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
				result['summary'] = installed.summary   # take the current one
				result['description'] = installed.description
				result['installed_version'] = installed.version
				result['size'] = installed.installed_size
				if package.is_upgradable:
					result['candidate_version'] = candidate.version
			else:
				del result['upgradable']  # not installed: don't show 'upgradable' at all
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
				size = float(size) / 1000  # MB, not MiB
			else:
				size = size * 1000  # once too often
			if size == int(size):
				format_string = '%d %s'
			else:
				format_string = '%.2f %s'
			result['size'] = format_string % (size, byte_mod)

		return result

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

	@sanitize_list(StringSanitizer())
	@multi_response(single_values=True)
	def components_get(self, iterator, component_id):
		# be as current as possible.
		self.uu.ucr_reinit()
		self.ucr.load()
		for component_id in iterator:
			yield self.component_manager.component(component_id)

	@sanitize_list(DictSanitizer({'object': advanced_components_sanitizer}))
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
	components_add = sanitize_list(DictSanitizer({'object': add_components_sanitizer}))(components_put)
	components_add.__name__ = 'components_add'

	@sanitize_list(StringSanitizer())
	@multi_response(single_values=True)
	def components_del(self, iterator, component_id):
		for component_id in iterator:
			yield self.component_manager.remove(component_id)
		self.package_manager.update()

	@multi_response
	def settings_get(self, iterator):
		# *** IMPORTANT *** Our UCR copy must always be current. This is not only
		#	to catch up changes made via other channels (ucr command line etc),
		#	but also to reflect the changes we have made ourselves!
		self.ucr.load()

		for _ in iterator:
			yield {
				'unmaintained': self.ucr.is_true('repository/online/unmaintained', False),
				'server': self.ucr.get('repository/online/server', ''),
				'prefix': self.ucr.get('repository/online/prefix', ''),
			}

	@sanitize_list(DictSanitizer({'object': basic_components_sanitizer}),
		min_elements=1, max_elements=1  # moduleStore with one element...
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
			return [{'message': str(e), 'status': constants.PUT_WRITE_ERROR}]

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
			response = {'message': msg, 'status': constants.PUT_UPDATER_ERROR}
			# if nothing was committed, we want a different type of error code,
			# just to appropriately inform the user
			if changed:
				response['status'] = constants.PUT_UPDATER_NOREPOS
			return [response]
		except:
			info = sys.exc_info()
			emsg = '%s: %s' % info[:2]
			MODULE.warn("   !! Updater error [%s]: %s" % (emsg))
			return [{'message': str(info[1]), 'status': constants.PUT_UPDATER_ERROR}]
		return [{'status': constants.PUT_SUCCESS}]
