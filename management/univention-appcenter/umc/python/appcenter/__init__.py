#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: software management
#
# Copyright 2011-2021 Univention GmbH
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

# standard library
import os
import locale
import time
from contextlib import contextmanager
import logging
from base64 import encodestring
from threading import Thread
from json import load

# related third party
import notifier
import notifier.threads
import apt  # for independent apt.Cache
import json

# univention
from univention.lib.package_manager import PackageManager, LockError
from univention.lib.umc import Client, ConnectionError, HTTPError, Forbidden
from univention.management.console.log import MODULE
from univention.management.console.modules.decorators import simple_response, sanitize, sanitize_list, multi_response, require_password
from univention.management.console.modules.mixins import ProgressMixin
from univention.management.console.modules.sanitizers import PatternSanitizer, MappingSanitizer, DictSanitizer, StringSanitizer, ChoicesSanitizer, ListSanitizer, BooleanSanitizer
from univention.updater.tools import UniventionUpdater
from univention.updater.errors import ConfigurationError
import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.appcenter.actions import get_action
from univention.appcenter.exceptions import Abort, NetworkError, AppCenterError
from univention.appcenter.packages import reload_package_manager, get_package_manager, package_lock, LOCK_FILE
from univention.appcenter.app_cache import Apps, AppCenterCache, default_server
from univention.appcenter.udm import _update_modules
from univention.appcenter.utils import docker_is_running, call_process, docker_bridge_network_conflict, send_information, app_is_running, find_hosts_for_master_packages, get_local_fqdn, resolve_dependencies
from univention.appcenter.install_checks import check
from univention.appcenter.log import get_base_logger, log_to_logfile
from univention.appcenter.ucr import ucr_instance, ucr_save
from univention.appcenter.settings import FileSetting, PasswordFileSetting

# local application
from .sanitizers import error_handling, AppSanitizer, basic_components_sanitizer, advanced_components_sanitizer, add_components_sanitizer
from .util import install_opener, ComponentManager, set_save_commit_load
from .constants import ONLINE_BASE, PUT_WRITE_ERROR, PUT_UPDATER_ERROR, PUT_SUCCESS, PUT_UPDATER_NOREPOS

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


def require_apps_update(func):
	def _deferred(self, *args, **kwargs):
		if not self.update_applications_done:
			self.update_applications()
		return func(self, *args, **kwargs)
	return _deferred


class Instance(umcm.Base, ProgressMixin):
	def init(self):
		os.umask(0o022)  # umc umask is too restrictive for app center as it creates a lot of files in docker containers
		self.ucr = ucr_instance()

		self.update_applications_done = False
		install_opener(self.ucr)
		self._is_working = False
		self._remote_progress = {}

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
		get_package_manager._package_manager = self.package_manager

		# build cache
		_update_modules()
		get_action('list').get_apps()

		# not initialize here: error prone due to network errors and also kinda slow
		self._uu = None
		self._cm = None

		# in order to set the correct locale
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

	def get_updater(self):
		if self._uu is None:
			self._uu = UniventionUpdater(False)
		return self._uu

	def get_component_manager(self):
		if self._cm is None:
			self._cm = ComponentManager(self.ucr, self.get_updater())
		return self._cm

	def error_handling(self, etype, exc, etraceback):
		error_handling(etype, exc, etraceback)
		return super(Instance, self).error_handling(exc, etype, etraceback)

	@simple_response
	def version(self, version=None):
		info = get_action('info')
		ret = info.get_compatibility()
		if not info.is_compatible(version):
			raise umcm.UMC_Error('The App Center version of the requesting host is not compatible with the version of %s (%s)' % (get_local_fqdn(), ret))
		return ret

	@sanitize(
		version=StringSanitizer(required=True),
		function=StringSanitizer(required=False),
	)
	@simple_response
	def version2(self, version, function=None):
		info = get_action('info')
		return {'compatible': info.is_compatible(version, function=function), 'version': info.get_ucs_version()}

	def _remote_appcenter(self, host, function=None):
		info = get_action('info')
		opts = {'version': info.get_ucs_version()}
		if function is not None:
			opts['function'] = function
		try:
			client = Client(host, self.username, self.password)
			response = client.umc_command('appcenter/version2', opts)
		except (HTTPError) as exc:
			raise umcm.UMC_Error(_('Problems connecting to {0} ({1}). Please update {0}!').format(host, exc.message))
		except (ConnectionError, Exception) as exc:
			raise umcm.UMC_Error(_('Problems connecting to {} ({}).').format(host, str(exc)))
		err_msg = _('The App Center version of the this host ({}) is not compatible with the version of {} ({})').format(opts['version'], host, response.result.get('version'))
		# i guess this is kind of bad
		if response.status is not 200:
			raise umcm.UMC_Error(err_msg)
		# remote says he is not compatible
		if response.result.get('compatible', True) is False:
			raise umcm.UMC_Error(err_msg)
		# i'm not compatible
		if not info.is_compatible(response.result.get('version')):
			raise umcm.UMC_Error(err_msg)
		return client

	@sanitize(
		apps=ListSanitizer(AppSanitizer(), required=True),
		action=ChoicesSanitizer(['install', 'upgrade', 'remove'], required=True)
	)
	@simple_response
	def resolve(self, apps, action):
		ret = {}
		ret['apps'] = resolve_dependencies(apps, action)
		ret['autoinstalled'] = [app.id for app in ret['apps'] if app.id not in [a.id for a in apps]]
		apps = ret['apps']
		ret['errors'], ret['warnings'] = check(apps, action)
		domain = get_action('domain')
		ret['apps'] = domain.to_dict(apps)
		ret['settings'] = {}
		self.ucr.load()
		for app in apps:
			ret['settings'][app.id] = self._get_config(app, action.title())
		return ret

	@require_apps_update
	@require_password
	@sanitize(
		apps=ListSanitizer(AppSanitizer(), required=True),
		auto_installed=ListSanitizer(required=True),
		action=ChoicesSanitizer(['install', 'upgrade', 'remove'], required=True),
		hosts=DictSanitizer({}, required=True),
		settings=DictSanitizer({}, required=True),
		dry_run=BooleanSanitizer(),
	)
	@simple_response(with_progress=True)
	def run(self, progress, apps, auto_installed, action, hosts, settings, dry_run):
		localhost = '{hostname}.{domainname}'.format(**self.ucr)
		ret = {}
		for app in apps:
			host = hosts[app.id]
			_settings = settings[app.id]
			_auto_installed = app.id in auto_installed
			if host == localhost:
				if dry_run:
					ret[app.id] = self._run_local_dry_run(app, action, _settings, progress)
				else:
					ret[app.id] = self._run_local(app, action, _settings, progress)
			else:
				if dry_run:
					ret[app.id] = self._run_remote_dry_run(host, app, action, _auto_installed, _settings, progress)
				else:
					ret[app.id] = self._run_remote(host, app, action, _auto_installed, _settings, progress)
			if not dry_run:
				if not ret[app.id]['success']:
					break
		return ret

	def _run_local_dry_run(self, app, action, settings, progress):
		progress.title = _('%s: Running tests') % app.name
		ret = {}
		ret['errors'], ret['warnings'] = check([app], action)
		ret['errors'].pop('must_have_no_unmet_dependencies', None)  # has to be resolved prior to this call!
		action = get_action(action)()
		args = action._build_namespace(app=app, dry_run=True, install_master_packages_remotely=False, only_master_packages=False)
		result = action.dry_run(app, args)
		if result is not None:
			ret.update(result)
		return ret

	def _run_local(self, app, action, settings, progress):
		kwargs = {
			'noninteractive': True,
			'skip_checks': ['shall_have_enough_ram', 'shall_only_be_installed_in_ad_env_with_password_service', 'must_not_have_concurrent_operation'],
			'set_vars': settings,
		}
		if action == 'install':
			progress.title = _('Installing %s') % (app.name,)
		elif action == 'remove':
			progress.title = _('Uninstalling %s') % (app.name,)
		elif action == 'upgrade':
			progress.title = _('Upgrading %s') % (app.name,)
		action = get_action(action)
		handler = UMCProgressHandler(progress)
		handler.setLevel(logging.INFO)
		action.logger.addHandler(handler)
		try:
			success = action.call(app=[app], username=self.username, password=self.password, **kwargs)
			return {'success': success}
		except AppCenterError as exc:
			raise umcm.UMC_Error(str(exc), result=dict(
				display_feedback=True,
				title='%s %s' % (exc.title, exc.info)))
		finally:
			action.logger.removeHandler(handler)

	def _run_remote_dry_run(self, host, app, action, auto_installed, settings, progress):
		return self._run_remote_logic(host, app, action, auto_installed, settings, progress, dry_run=True)

	def _run_remote(self, host, app, action, auto_installed, settings, progress):
		return self._run_remote_logic(host, app, action, auto_installed, settings, progress, dry_run=False)

	def _run_remote_logic(self, host, app, action, auto_installed, settings, progress, dry_run):
		progress.title = _('%s: Connecting to %s') % (app.name, host)
		client = self._remote_appcenter(host, function='appcenter/run')
		auto_installed = [app.id] if auto_installed else []
		opts = {'apps': [str(app)], 'auto_installed': auto_installed, 'action': action, 'hosts': {app.id: host}, 'settings': {app.id: settings}, 'dry_run': dry_run}
		progress_id = client.umc_command('appcenter/run', opts).result['id']
		while True:
			result = client.umc_command('appcenter/docker/progress', {'progress_id': progress_id}).result
			if result['finished']:
				return result['result'][app.id]
			progress.title = result['title']
			progress.intermediate.extend(result['intermediate'])
			progress.message = result['message']
			time.sleep(result['retry_after'] / 1000.0)

	@simple_response
	def query(self, quick=False):
		query_cache_file = '/var/cache/univention-appcenter/umc-query.json'
		if quick:
			try:
				with open(query_cache_file) as fd:
					return json.load(fd)
			except (EnvironmentError, ValueError) as exc:
				MODULE.error('Error returning cached query: %s' % exc)
				return []
		self.update_applications()
		self.ucr.load()
		reload_package_manager()
		list_apps = get_action('list')
		domain = get_action('domain')
		apps = list_apps.get_apps()
		if self.ucr.is_true('appcenter/docker', True):
			if not self._test_for_docker_service():
				raise umcm.UMC_Error(_('The docker service is not running! The App Center will not work properly.') + ' ' + _('Make sure docker.io is installed, try starting the service with "service docker start".'))
		info = domain.to_dict(apps)
		with open(query_cache_file, 'w') as fd:
			json.dump(info, fd)
		return info

	def update_applications(self):
		if self.ucr.is_true('appcenter/umc/update/always', True):
			update = get_action('update')
			try:
				update.call()
			except NetworkError as err:
				raise umcm.UMC_Error(str(err))
			except Abort:
				pass
			self.update_applications_done = True

	def _test_for_docker_service(self):
		if docker_bridge_network_conflict():
			msg = _('A conflict between the system network settings and the docker bridge default network has been detected.') + '\n\n'
			msg += _('Please either configure a different network for the docker bridge by setting the UCR variable docker/daemon/default/opts/bip to a different network and restart the system,') + ' '
			msg += _('or disable the docker support in the AppCenter by setting appcenter/docker to false.')
			raise umcm.UMC_Error(msg)
		if not docker_is_running():
			MODULE.warn('Docker is not running! Trying to start it now...')
			call_process(['invoke-rc.d', 'docker', 'start'])
			if not docker_is_running():
				return False
		return True

	@simple_response
	def suggestions(self, version):
		try:
			cache = AppCenterCache.build(server=default_server())
			cache_file = cache.get_cache_file('.suggestions.json')
			with open(cache_file) as fd:
				json = load(fd)
		except (EnvironmentError, ValueError):
			raise umcm.UMC_Error(_('Could not load suggestions.'))
		else:
			try:
				return json[version]
			except (KeyError, AttributeError):
				raise umcm.UMC_Error(_('Unexpected suggestions data.'))

	@simple_response
	def enable_docker(self):
		if self._test_for_docker_service():
			ucr_save({'appcenter/docker': 'enabled'})
		else:
			raise umcm.UMC_Error(_('Unable to start the docker service!') + ' ' + _('Make sure docker.io is installed, try starting the service with "service docker start".'))

	@require_apps_update
	@require_password
	@simple_response(with_progress=True)
	def sync_ldap(self):
		register = get_action('register')
		register.call(username=self.username, password=self.password)

	# used in updater-umc
	@simple_response
	def get_by_component_id(self, component_id):
		domain = get_action('domain')
		if isinstance(component_id, list):
			requested_apps = [Apps().find_by_component_id(cid) for cid in component_id]
			return domain.to_dict(requested_apps)
		else:
			app = Apps().find_by_component_id(component_id)
			if app:
				return domain.to_dict([app])[0]
			else:
				raise umcm.UMC_Error(_('Could not find an application for %s') % component_id)

	# used in updater-umc
	@simple_response
	def app_updates(self):
		upgrade = get_action('upgrade')
		domain = get_action('domain')
		return domain.to_dict(list(upgrade.iter_upgradable_apps()))

	@sanitize(application=StringSanitizer(minimum=1, required=True))
	@simple_response
	def get(self, application):
		list_apps = get_action('list')
		domain = get_action('domain')
		apps = list_apps.get_apps()
		for app in apps:
			if app.id == application:
				break
		else:
			app = None
		if app is None:
			raise umcm.UMC_Error(_('Could not find an application for %s') % (application,))
		return domain.to_dict([app])[0]

	@sanitize(app=AppSanitizer(required=True))
	@simple_response
	def config(self, app, phase):
		self.ucr.load()
		return self._get_config(app, phase)

	def _get_config(self, app, phase):
		autostart = self.ucr.get('%s/autostart' % app.id, 'yes')
		is_running = app_is_running(app)
		values = {}
		for setting in app.get_settings():
			if phase in setting.show or phase in setting.show_read_only:
				value = setting.get_value(app, phase)
				if isinstance(setting, FileSetting) and not isinstance(setting, PasswordFileSetting):
					if value:
						value = encodestring(value).rstrip()
				values[setting.name] = value
		return {
			'autostart': autostart,
			'is_running': is_running,
			'values': values,
		}

	@sanitize(app=AppSanitizer(required=True), values=DictSanitizer({}))
	@simple_response(with_progress=True)
	def configure(self, progress, app, values, autostart=None):
		for setting in app.get_settings():
			if isinstance(setting, FileSetting) and not isinstance(setting, PasswordFileSetting):
				if values.get(setting.name):
					values[setting.name] = values[setting.name].decode('base64')
		configure = get_action('configure')
		handler = UMCProgressHandler(progress)
		handler.setLevel(logging.INFO)
		configure.logger.addHandler(handler)
		try:
			return configure.call(app=app, set_vars=values, autostart=autostart)
		finally:
			configure.logger.removeHandler(handler)

	@sanitize(app=AppSanitizer(required=True), mode=ChoicesSanitizer(['start', 'stop']))
	@simple_response
	def app_service(self, app, mode):
		service = get_action(mode)
		service.call(app=app)

	@sanitize(app=AppSanitizer(required=False), action=ChoicesSanitizer(['get', 'buy', 'search', 'vote']), value=StringSanitizer())
	@simple_response
	def track(self, app, action, value):
		send_information(action, app=app, value=value)

	def invoke_dry_run(self, request):
		request.options['only_dry_run'] = True
		self.invoke(request)

	@require_password
	@sanitize(
		host=StringSanitizer(required=True),
		function=ChoicesSanitizer(['install', 'update', 'uninstall'], required=True),
		app=StringSanitizer(required=True),
		force=BooleanSanitizer(),
		values=DictSanitizer({})
	)
	@simple_response(with_progress=True)
	def invoke_remote_docker(self, host, function, app, force, values, progress):
		options = {'function': function, 'app': app, 'force': force, 'values': values}
		client = Client(host, self.username, self.password)
		result = client.umc_command('appcenter/docker/invoke', options).result
		self._remote_progress[progress.id] = client, result['id']

	@simple_response
	def remote_progress(self, progress_id):
		try:
			client, remote_progress_id = self._remote_progress[progress_id]
		except KeyError:
			# actually happens: before invoke_remote_docker is finished, remote_progress is already called
			return {}
		else:
			return client.umc_command('appcenter/docker/progress', {'progress_id': remote_progress_id}).result

	@require_apps_update
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
		for setting in app.get_settings():
			if isinstance(setting, FileSetting) and not isinstance(setting, PasswordFileSetting):
				if values.get(setting.name):
					values[setting.name] = values[setting.name].decode('base64')
		progress.title = _('%s: Running tests') % app.name
		serious_problems = False
		if function == 'upgrade':
			_original_app = app
			# TODO support app_id=version
			app = Apps().find_candidate(app)
		if app is None:
			# Bug #44384: Under mysterious circumstances, app may be None after the .find_candidate()
			# This may happen in global App Center when the system the user is logged in has different ini files
			# than the system the App shall be upgraded on. E.g., in mixed appcenter / appcenter-test environments
			app = _original_app
			errors, warnings = {'must_have_candidate': False}, {}
		else:
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
			kwargs = {'noninteractive': True, 'skip_checks': ['shall_have_enough_ram', 'shall_only_be_installed_in_ad_env_with_password_service', 'must_not_have_concurrent_operation'], 'set_vars': values}
			if function == 'install':
				progress.title = _('Installing %s') % (app.name,)
			elif function == 'uninstall':
				progress.title = _('Uninstalling %s') % (app.name,)
			elif function == 'upgrade':
				progress.title = _('Upgrading %s') % (app.name,)
			action = get_action(function)
			handler = UMCProgressHandler(progress)
			handler.setLevel(logging.INFO)
			action.logger.addHandler(handler)
			try:
				result['success'] = action.call(app=[app], username=self.username, password=self.password, **kwargs)
			except AppCenterError as exc:
				raise umcm.UMC_Error(str(exc), result=dict(
					display_feedback=True,
					title='%s %s' % (exc.title, exc.info)))
			finally:
				action.logger.removeHandler(handler)
		return result

	@contextmanager
	def locked(self):
		try:
			if self._working():
				raise LockError()
			with package_lock():
				yield
		except LockError:
			raise umcm.UMC_Error(_('Another package operation is in progress'))

	@require_apps_update
	@require_password
	@sanitize(
		function=ChoicesSanitizer(['install', 'uninstall', 'update', 'install-schema', 'update-schema', 'upgrade', 'upgrade-schema', 'remove'], required=True),
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
		# if you add new arguments that change the behavior
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
			function = 'upgrade'
		if function == 'uninstall':
			function = 'remove'

		app_id = request.options.get('application')
		app_version = None
		if '=' in app_id:
			app_id, app_version = tuple(app_id.split('=', 1))
		app = Apps().find(app_id, app_version=app_version)
		if app is None:
			raise umcm.UMC_Error(_('Could not find an application for %s') % (app_id,))
		force = request.options.get('force')
		values = request.options.get('values')
		only_dry_run = request.options.get('only_dry_run')
		dont_remote_install = request.options.get('dont_remote_install')
		only_master_packages = send_as.endswith('schema')
		MODULE.process('Try to %s (%s) %s on %s. Force? %r. Only Primary/Backup Node packages? %r. Prevent installation on other systems? %r. Only dry run? %r.' % (function, send_as, app_id, host, force, only_master_packages, dont_remote_install, only_dry_run))

		# REMOTE invocation!
		if host and host != self.ucr.get('hostname') and host != '%s.%s' % (self.ucr.get('hostname'), self.ucr.get('domainname')):
			try:
				client = Client(host, self.username, self.password)
				# shortening hostname for compatability
				version = get_action('info').get_ucs_version()
				remote_version = client.umc_command('appcenter/version2', {'version': version}).result.get('version')
				if remote_version <= '4.4-3 errata482':
					host_shortname = host.split('.')[0]
					request.options['host'] = host_shortname
					client = Client(host_shortname, self.username, self.password)

				result = client.umc_command('appcenter/invoke', request.options).result
			except (ConnectionError, HTTPError) as exc:
				MODULE.error('Error during remote appcenter/invoke: %s' % (exc,))
				result = {
					'unreachable': [host],
					'master_unreachable': True,
					'serious_problems': True,
					'software_changes_computed': True,  # not really...
				}
			else:
				if result['can_continue']:
					def _thread_remote(_client):
						with self.is_working():
							self._query_remote_progress(_client)

					def _finished_remote(thread, result):
						if isinstance(result, BaseException):
							MODULE.warn('Exception during %s %s: %s' % (function, app_id, str(result)))
					thread = notifier.threads.Simple('invoke', notifier.Callback(_thread_remote, client), _finished_remote)
					thread.run()
			self.finished(request.id, result)
			return

		# make sure that the application can be installed/updated
		action = get_action(function)()
		args = action._build_namespace(app=[app], username=self.username, password=self.password, noninteractive=True, skip_checks=['shall_have_enough_ram', 'shall_only_be_installed_in_ad_env_with_password_service', 'must_not_have_concurrent_operation'], send_info=not only_master_packages, set_vars=values, dry_run=True, install_master_packages_remotely=False, only_master_packages=only_master_packages)
		if only_master_packages:
			args.skip_checks.append('must_not_be_installed')

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
		if not app:
			MODULE.process('Application not found: %s' % app_id)
			can_continue = False
		if can_continue and not only_master_packages:
			if function == 'upgrade':
				# TODO support app_id=version
				app = Apps().find_candidate(app)
			if app is None:
				forbidden, warnings = {'must_have_candidate': False}, {}
			else:
				forbidden, warnings = app.check(function)
			if forbidden:
				MODULE.process('Cannot %s %s: %r' % (function, app_id, forbidden))
				result['invokation_forbidden_details'] = forbidden
				can_continue = False
				serious_problems = True
			if warnings:
				MODULE.process('Warning trying to %s %s: %r' % (function, app_id, forbidden))
				result['invokation_warning_details'] = warnings
				if not force:
					# don't stop "immediately".
					#   compute the package changes!
					delayed_can_continue = False
		result['serious_problems'] = serious_problems
		result['can_continue'] = can_continue
		if can_continue:
			with self.locked():
				if can_continue and function in ('install', 'upgrade'):
					result.update(self._install_dry_run_remote(app, function, dont_remote_install, force))
					serious_problems = bool(result['master_unreachable'] or result['serious_problems_with_hosts'])
					if serious_problems:
						args.dry_run = True
					result.update(action.dry_run(app, args))
					result['software_changes_computed'] = True
					serious_problems = bool(result['broken'] or serious_problems)
					if serious_problems or (not force and (result['unreachable'] or result['install'] or result['remove'] or result['problems_with_hosts'])):
						can_continue = False
				elif can_continue and function in ('remove',) and not force:
					result.update(action.dry_run(app, args))
					result['software_changes_computed'] = True
					can_continue = False
				can_continue = can_continue and delayed_can_continue and not only_dry_run
				result['serious_problems'] = serious_problems
				result['can_continue'] = can_continue

				if can_continue and not only_dry_run:
					def _thread(module, app, function):
						with module.is_working():
							if not dont_remote_install and function != 'remove':
								self._install_master_packages_on_hosts(app, function)
							with module.package_manager.no_umc_restart(exclude_apache=True):
								try:
									args.dry_run = False
									args.install_master_packages_remotely = False
									return action.call_with_namespace(args)
								except AppCenterError as exc:
									raise umcm.UMC_Error(str(exc), result=dict(
										display_feedback=True,
										title='%s %s' % (exc.title, exc.info)))

					def _finished(thread, result):
						if isinstance(result, BaseException):
							MODULE.warn('Exception during %s %s: %s' % (function, app_id, str(result)))
					thread = notifier.threads.Simple('invoke', notifier.Callback(_thread, self, app, function), _finished)
					thread.run()
		self.finished(request.id, result)

	def _install_master_packages_on_hosts(self, app, function):
		if function.startswith('upgrade'):
			remote_function = 'update-schema'
		else:
			remote_function = 'install-schema'
		master_packages = app.default_packages_master
		if not master_packages:
			return
		hosts = find_hosts_for_master_packages()
		all_hosts_count = len(hosts)
		package_manager = get_package_manager()
		package_manager.set_max_steps(all_hosts_count * 200)  # up to 50% if all hosts are installed
		# maybe we already installed local packages (on master)
		if self.ucr.get('server/role') == 'domaincontroller_master':
			# TODO: set_max_steps should reset _start_steps. need function like set_start_steps()
			package_manager.progress_state._start_steps = all_hosts_count * 100
		for host, host_is_master in hosts:
			package_manager.progress_state.info(_('Installing LDAP packages on %s') % host)
			try:
				if not self._install_master_packages_on_host(app, remote_function, host):
					error_message = 'Unable to install %r on %s. Check /var/log/univention/management-console-module-appcenter.log on the host and this server. All errata updates have been installed on %s?' % (master_packages, host, host)
					raise Exception(error_message)
			except Exception as e:
				MODULE.error('%s: %s' % (host, e))
				if host_is_master:
					role = 'Primary Directory Node'
				else:
					role = 'Backup Directory Node'
				# ATTENTION: This message is not localised. It is parsed by the frontend to markup this message! If you change this message, be sure to do the same in AppCenterPage.js
				package_manager.progress_state.error('Installing extension of LDAP schema for %s seems to have failed on %s %s' % (app.component_id, role, host))
				if host_is_master:
					raise  # only if host_is_master!
			finally:
				package_manager.add_hundred_percent()

	def _install_master_packages_on_host(self, app, function, host):
		client = Client(host, self.username, self.password)
		result = client.umc_command('appcenter/invoke', {'function': function, 'application': app.id, 'force': True, 'dont_remote_install': True}).result
		if result['can_continue']:
			all_errors = self._query_remote_progress(client)
			return len(all_errors) == 0
		else:
			MODULE.warn('%r' % result)
			return False

	def _install_dry_run_remote(self, app, function, dont_remote_install, force):
		MODULE.process('Invoke install_dry_run_remote')
		self.ucr.load()
		if function.startswith('upgrade'):
			remote_function = 'update-schema'
		else:
			remote_function = 'install-schema'

		master_packages = app.default_packages_master

		# connect to Primary/Backup Nodes
		unreachable = []
		hosts_info = {}
		remote_info = {
			'master_unreachable': False,
			'problems_with_hosts': False,
			'serious_problems_with_hosts': False,
		}
		dry_run_threads = []
		info = get_action('info')
		if master_packages and not dont_remote_install:
			hosts = find_hosts_for_master_packages()
			# checking remote host is I/O heavy, so use threads
			#   "global" variables: unreachable, hosts_info, remote_info

			def _check_remote_host(app_id, host, host_is_master, username, password, force, remote_function):
				MODULE.process('Starting dry_run for %s on %s' % (app_id, host))
				MODULE.process('%s: Connecting...' % host)
				try:
					client = Client(host, username, password)
				except (ConnectionError, HTTPError) as exc:
					MODULE.warn('_check_remote_host: %s: %s' % (host, exc))
					unreachable.append(host)
					if host_is_master:
						remote_info['master_unreachable'] = True
				else:
					MODULE.process('%s: ... done' % host)
					host_info = {}
					MODULE.process('%s: Getting version...' % host)
					try:
						host_version = client.umc_command('appcenter/version', {'version': info.get_compatibility()}).result
					except Forbidden:
						# command is not yet known (older app center)
						MODULE.process('%s: ... forbidden!' % host)
						host_version = None
					except (ConnectionError, HTTPError) as exc:
						MODULE.warn('%s: Could not get appcenter/version: %s' % (exc,))
						raise
					except Exception as exc:
						MODULE.error('%s: Exception: %s' % (host, exc))
						raise
					MODULE.process('%s: ... done' % host)
					host_info['compatible_version'] = info.is_compatible(host_version)
					MODULE.process('%s: Invoking %s ...' % (host, remote_function))
					try:
						host_info['result'] = client.umc_command('appcenter/invoke_dry_run', {
							'function': remote_function,
							'application': app_id,
							'force': force,
							'dont_remote_install': True,
						}).result
					except Forbidden:
						# command is not yet known (older app center)
						MODULE.process('%s: ... forbidden!' % host)
						host_info['result'] = {'can_continue': False, 'serious_problems': False}
					except (ConnectionError, HTTPError) as exc:
						MODULE.warn('Could not get appcenter/version: %s' % (exc,))
						raise
					MODULE.process('%s: ... done' % host)
					if not host_info['compatible_version'] or not host_info['result']['can_continue']:
						remote_info['problems_with_hosts'] = True
						if host_info['result']['serious_problems'] or not host_info['compatible_version']:
							remote_info['serious_problems_with_hosts'] = True
					hosts_info[host] = host_info
				MODULE.process('Finished dry_run for %s on %s' % (app_id, host))

			for host, host_is_master in hosts:
				thread = Thread(target=_check_remote_host, args=(app.id, host, host_is_master, self.username, self.password, force, remote_function))
				thread.start()
				dry_run_threads.append(thread)

		result = {}

		for thread in dry_run_threads:
			thread.join()
		MODULE.process('All %d threads finished' % (len(dry_run_threads)))

		result['unreachable'] = unreachable
		result['hosts_info'] = hosts_info
		result.update(remote_info)
		return result

	def _query_remote_progress(self, client):
		all_errors = set()
		number_failures = 0
		number_failures_max = 20
		host = client.hostname
		while True:
			try:
				result = client.umc_command('appcenter/progress').result
			except (ConnectionError, HTTPError) as exc:
				MODULE.warn('%s: appcenter/progress returned an error: %s' % (host, exc))
				number_failures += 1
				if number_failures >= number_failures_max:
					MODULE.error('%s: Remote App Center cannot be contacted for more than %d seconds. Maybe just a long Apache Restart? Presume failure! Check logs on remote machine, maybe installation was successful.' % number_failures_max)
					return False
				time.sleep(1)
				continue
			else:
				# everything okay. reset "timeout"
				number_failures = 0
			MODULE.info('Result from %s: %r' % (host, result))
			info = result['info']
			steps = result['steps']
			errors = ['%s: %s' % (host, error) for error in result['errors']]
			if info:
				self.package_manager.progress_state.info(info)
			if steps:
				steps = float(steps)  # bug in package_manager in 3.1-0: int will result in 0 because of division and steps < max_steps
				self.package_manager.progress_state.percentage(steps)
			for error in errors:
				if error not in all_errors:
					self.package_manager.progress_state.error(error)
					all_errors.add(error)
			if result['finished'] is True:
				break
			time.sleep(0.1)
		return all_errors

	def keep_alive(self, request):
		''' Fix for Bug #30611: UMC kills appcenter module
		if no request is sent for $(ucr get umc/module/timeout).
		this happens if a user logs out during a very long installation.
		this function will be run by the frontend to always have one connection open
		to prevent killing the module. '''
		def _thread():
			while self._working():
				time.sleep(1)

		def _finished(thread, result):
			success = not isinstance(result, BaseException)
			if not success:
				MODULE.warn('Exception during keep_alive: %s' % result)
			self.finished(request.id, success)
		thread = notifier.threads.Simple('keep_alive', notifier.Callback(_thread), _finished)
		thread.run()

	@simple_response
	def ping(self):
		return True

	@simple_response
	def buy(self, application):
		app = Apps().find(application)
		if not app or not app.shop_url:
			return None
		ret = {}
		ret['key_id'] = self.ucr.get('license/uuid')
		ret['ucs_version'] = self.ucr.get('version/version')
		ret['app_id'] = app.id
		ret['app_version'] = app.version
		# ret['locale'] = locale.getlocale()[0] # done by frontend
		ret['user_count'] = None  # FIXME: get users and computers from license
		ret['computer_count'] = None
		return ret

	@simple_response
	def enable_disable_app(self, application, enable=True):
		app = Apps().find(application)
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

	@sanitize(
		function=MappingSanitizer({
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

	@sanitize(
		function=MappingSanitizer({
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
					thread = notifier.threads.Simple('invoke', notifier.Callback(_thread, self.package_manager, function, packages), _finished)
					thread.run()
				else:
					self.package_manager.set_finished()  # nothing to do, ready to take new commands
		except LockError:
			# make it thread safe: another process started a package manager
			# this module instance already has a running package manager
			raise umcm.UMC_Error(_('Another package operation is in progress'))

	@contextmanager
	def is_working(self):
		self._is_working = True
		yield
		self._is_working = False

	def _working(self):
		return self._is_working or os.path.exists(LOCK_FILE) or not self.package_manager.progress_state._finished

	@simple_response
	def working(self):
		# TODO: PackageManager needs is_idle() or something
		#   preferably the package_manager can tell what is currently executed:
		#   package_manager.is_working() => False or _('Installing PKG')
		return self._working()

	@simple_response
	def custom_progress(self):
		timeout = 5
		ret = self.package_manager.poll(timeout)
		ret['finished'] = not self._working()
		return ret

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
		self.get_updater().ucr_reinit()
		self.ucr.load()

		return [
			self.get_component_manager().component(comp.name)
			for comp in self.get_updater().get_components(all=True)
		]

	@sanitize_list(StringSanitizer())
	@multi_response(single_values=True)
	def components_get(self, iterator, component_id):
		# be as current as possible.
		self.get_updater().ucr_reinit()
		self.ucr.load()
		for component_id in iterator:
			yield self.get_component_manager().component(component_id)

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
		with set_save_commit_load(self.ucr) as super_ucr:
			for object, in iterator:
				yield self.get_component_manager().put(object, super_ucr)
		self.package_manager.update()

	# do the same as components_put (update)
	# but don't allow adding an already existing entry
	components_add = sanitize_list(DictSanitizer({'object': add_components_sanitizer}))(components_put)
	components_add.__name__ = 'components_add'

	@sanitize_list(StringSanitizer())
	@multi_response(single_values=True)
	def components_del(self, iterator, component_id):
		for component_id in iterator:
			yield self.get_component_manager().remove(component_id)
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

	@sanitize_list(
		DictSanitizer({'object': basic_components_sanitizer}),
		min_elements=1,
		max_elements=1  # moduleStore with one element...
	)
	@multi_response
	def settings_put(self, iterator, object):
		# FIXME: returns values although it should yield (multi_response)
		changed = False
		# Set values into our UCR copy.
		try:
			with set_save_commit_load(self.ucr) as super_ucr:
				for object, in iterator:
					for key, value in object.items():
						MODULE.info("   ++ Setting new value for '%s' to '%s'" % (key, value))
						super_ucr.set_registry_var('%s/%s' % (ONLINE_BASE, key), value)
				changed = super_ucr.changed()
		except Exception as e:
			MODULE.warn("   !! Writing UCR failed: %s" % str(e))
			return [{'message': str(e), 'status': PUT_WRITE_ERROR}]

		self.package_manager.update()

		# Bug #24878: emit a warning if repository is not reachable
		try:
			updater = self.get_updater()
			for line in updater.print_version_repositories().split('\n'):
				if line.strip():
					break
			else:
				raise ConfigurationError()
		except ConfigurationError:
			msg = _("There is no repository at this server (or at least none for the current UCS version)")
			MODULE.warn("   !! Updater error: %s" % msg)
			response = {'message': msg, 'status': PUT_UPDATER_ERROR}
			# if nothing was committed, we want a different type of error code,
			# just to appropriately inform the user
			if changed:
				response['status'] = PUT_UPDATER_NOREPOS
			return [response]
		except BaseException as ex:
			MODULE.warn("   !! Updater error: %s" % (ex,))
			return [{'message': str(ex), 'status': PUT_UPDATER_ERROR}]
		return [{'status': PUT_SUCCESS}]
