#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app base module for installing, uninstalling, upgrading an app
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

import os.path
import shutil
from glob import glob
from getpass import getuser
import subprocess
from argparse import SUPPRESS, Action
from tempfile import NamedTemporaryFile
import traceback

from six import string_types
from six.moves import input

from univention.appcenter.app import App, DATA_DIR
from univention.appcenter.actions import StoreAppAction, get_action
from univention.appcenter.exceptions import Abort, NetworkError, AppCenterError, ParallelOperationInProgress
from univention.appcenter.actions.register import Register
from univention.appcenter.utils import get_locale, resolve_dependencies, call_process2
from univention.appcenter.ucr import ucr_get
from univention.appcenter.settings import SettingValueError
from univention.appcenter.packages import package_lock, LockError
from univention.appcenter.install_checks import get_requirement, check


class StoreConfigAction(Action):
	def __call__(self, parser, namespace, value, option_string=None):
		set_vars = {}
		for val in value:
			try:
				key, val = val.split('=', 1)
			except ValueError:
				parser.error('Could not parse %s. Use var=val. Skipping...' % val)
			else:
				set_vars[key] = val
		setattr(namespace, self.dest, set_vars)


class InstallRemoveUpgrade(Register):
	prescript_ext = None
	pre_readme = None
	post_readme = None

	def setup_parser(self, parser):
		super(Register, self).setup_parser(parser)
		parser.add_argument('--set', nargs='+', action=StoreConfigAction, metavar='KEY=VALUE', dest='set_vars', help='Sets the configuration variable. Example: --set some/variable=value some/other/variable="value 2"')
		parser.add_argument('--skip-checks', nargs='*', choices=[req.name for req in App._requirements if self.get_action_name() in req.actions], help=SUPPRESS)
		parser.add_argument('--do-not-configure', action='store_false', dest='configure', help=SUPPRESS)
		parser.add_argument('--do-not-update-certificates', action='store_false', dest='update_certificates', help=SUPPRESS)
		parser.add_argument('--do-not-call-join-scripts', action='store_false', dest='call_join_scripts', help=SUPPRESS)
		parser.add_argument('--do-not-send-info', action='store_false', dest='send_info', help=SUPPRESS)
		parser.add_argument('--autoinstalled', nargs='+', dest='autoinstalled', help=SUPPRESS)
		parser.add_argument('--dry-run', action='store_true', dest='dry_run', help='Perform only a dry-run. App state is not touched')
		parser.add_argument('app', nargs='+', action=StoreAppAction, help='The ID of the App')

	main = None  # no action by itself

	def _write_start_event(self, app, args):
		pass

	def _write_success_event(self, app, context_id, args):
		pass

	def _write_fail_event(self, app, context_id, status, args):
		pass

	def _call_action_hooks(self, directory):
		"""
		abstract method is empty, because there is no default hook for any
		action. The implementation has to be done in each derived class if
		needed.
		"""
		pass

	def _run_parts(self, directory):
		"""
		in order to call hooks we use run-parts, so that administrators can
		better comprehend what is done behind the scenes and test their script
		folders manually using that tool.
		"""
		if os.path.isdir(directory):
			(retval, output) = call_process2(["run-parts", directory])
			# self.log(output) is unnecessary, because call_process2 logs its
			# output, but if you are replacing call_process2 with something
			# different, please remember to to inform the user about the output
			# of the scripts!
		else:
			self.log('Potential script hook folder is unused: {folder}'.format(folder=directory))

	def do_it(self, args):
		i = -1
		apps = []
		try:
			try:
				action = self.get_action_name()
				apps = resolve_dependencies(args.app, action)
				for app in apps:
					self.log('Going to %s %s (%s)' % (action, app.name, app.version))
				new_apps = [app for app in apps if app.id not in [_a.id for _a in args.app]]
				new_apps_have_settings = False
				for app in new_apps:
					if app.get_settings():
						new_apps_have_settings = True
						self.fatal('Automatically added App %s has its own settings. You should explicitely mention this App. This way, you may (or may not) set settings for this App via --set.' % app)
				if new_apps_have_settings:
					self.fatal('Unable to %s. Aborting...' % action)
					return False
				if not args.autoinstalled:
					# save the installed status for those apps that were not explicitely given
					# but where added by resolving the dependencies
					args.autoinstalled = [app.id for app in new_apps]
				errors, warnings = check(apps, action)
				can_continue = self._handle_errors(args, errors, True)
				can_continue = self._handle_errors(args, warnings, fatal=not can_continue) and can_continue
				if can_continue and self.needs_credentials(app) and not self.check_user_credentials(args):
					can_continue = False
				if not can_continue:
					self.fatal('Unable to %s. Aborting...' % action)
					return False
				for app in apps:
					try:
						self._show_license(app, args)
						self._show_pre_readme(app, args)
					except Abort:
						self.warn('Cancelled...')
						return
			except Exception:
				trace = traceback.format_exc()
				if apps:
					for app in apps:
						self._send_information_on_app(app, 502, trace, args)
				else:
					self._send_information_on_app(None, 502, trace, args)
				raise
			for i, app in enumerate(apps):
				args.app = app
				success = self.do_it_once(app, args)
				if not success:
					break
			else:
				return True
			return False
		finally:
			not_touched = apps[i + 1:]
			if not_touched:
				self.warn('Failure will leave these apps untouched: %s' % ', '.join(app.id for app in not_touched))
			if i >= 0:
				for app in apps[:i]:
					try:
						self._show_post_readme(app, args)
					except Abort:
						pass
			upgrade_search = get_action('upgrade-search')
			upgrade_search.call_safe(app=apps, update=False)

	def _send_information_on_app(self, app, status, status_details, args):
		if args.send_info:
			try:
				# do not send more than 500 char of status_details
				if isinstance(status_details, string_types):
					status_details = status_details[-5000:]
				self._send_information(app, status, status_details)
			except NetworkError:
				self.log('Ignoring this error...')

	def do_it_once(self, app, args):
		status = 200
		status_details = None
		context_id = self._write_start_event(app, args)
		try:
			self._configure(app, args, run_script='no', scope='outside')
			if not self._call_prescript(app, args):
				self.fatal('Running prescript of %s failed. Aborting...' % app)
				status = 0
			else:
				try:
					try:
						with package_lock():
							if args.dry_run:
								self.dry_run(app, args)
							else:
								self._do_it(app, args)
					except LockError:
						raise ParallelOperationInProgress()
				except (Abort, KeyboardInterrupt) as exc:
					msg = str(exc)
					if msg:
						self.fatal(msg)
					self.warn('Aborting...')
					if exc.__class__ is KeyboardInterrupt:
						status = 401
					else:
						status = exc.code
						status_details = exc.get_exc_details()
				except Exception as exc:
					status = 500
					status_details = repr(exc)
					raise
		except AppCenterError as exc:
			status = exc.code
			raise
		else:
			return status == 200
		finally:
			if args.dry_run:
				pass
			elif status == 0:
				pass
			else:
				if status == 200:
					self._write_success_event(app, context_id, args)
					self._call_action_hooks(
						"{data_dir}/{app_id}/local/hooks/"
						"{when}-{action}.d".format(
							data_dir=DATA_DIR,
							app_id=app.id,
							action=self.get_action_name(),
							when="post"
						)
					)
				else:
					self._write_fail_event(app, context_id, status, args)
				if status != 200:
					self._revert(app, args)
				self._send_information_on_app(app, status, status_details, args)
				self._register_installed_apps_in_ucr()

	def needs_credentials(self, app):
		if os.path.exists(app.get_cache_file(self.prescript_ext)):
			return True
		if os.path.exists(app.get_cache_file('schema')):
			return True
		if os.path.exists(app.get_cache_file('attributes')) or app.generic_user_activation:
			return True
		if app.docker and app.docker_script_setup:
			return True
		return False

	def _handle_errors(self, args, errors, fatal):
		can_continue = True
		for error in errors:
			details = errors[error]
			try:
				requirement = get_requirement(error)
				try:
					message = requirement.__doc__ % details
				except TypeError:
					message = requirement.__doc__
			except KeyError:
				message = ''
			message = '(%s) %s' % (error, message or '')
			if args.skip_checks is not None and (error in args.skip_checks or args.skip_checks == []):
				self.log(message)
			else:
				if fatal:
					self.fatal(message)
				else:
					self.warn(message)
				can_continue = False
		if not can_continue:
			if fatal:
				return False
			else:
				if args.noninteractive:
					return True
				try:
					aggreed = input('Do you want to %s anyway [y/N]? ' % self.get_action_name())
				except (KeyboardInterrupt, EOFError):
					return False
				else:
					return aggreed.lower()[:1] in ['y', 'j']
		return True

	def _call_prescript(self, app, args, **kwargs):
		ext = self.prescript_ext
		self.debug('Calling prescript (%s)' % ext)
		if not ext:
			return True
		script = app.get_cache_file(ext)
		# check here to not bother asking for a password
		# otherwise self._call_script could handle it, too
		if not os.path.exists(script):
			self.debug('%s does not exist' % script)
			return True
		with NamedTemporaryFile('r') as error_file:
			with self._get_password_file(args) as pwdfile:
				if not pwdfile:
					self.warn('Could not get password')
					return False
				kwargs['version'] = app.version
				kwargs['error_file'] = error_file.name
				kwargs['binddn'] = self._get_userdn(args)
				kwargs['bindpwdfile'] = pwdfile
				locale = get_locale()
				if locale:
					kwargs['locale'] = locale
				success = self._call_cache_script(app, ext, **kwargs)
				if not success:
					for line in error_file:
						self.fatal(line)
				return success

	def _revert(self, app, args):
		pass

	def _do_it(self, app, args):
		raise NotImplementedError()

	def _show_license(self, app, args):
		self.log('Showing License agreement for %s' % app)
		if self._show_file(app, 'license_agreement', args, agree=True) is False:
			raise Abort()

	def _show_pre_readme(self, app, args):
		self.log('Showing README for %s' % app)
		if self._show_file(app, self.pre_readme, args, confirm=True) is False:
			raise Abort()

	def _show_post_readme(self, app, args):
		self.log('Showing README for %s' % app)
		if self._show_file(app, self.post_readme, args, confirm=True) is False:
			raise Abort()

	def _show_file(self, app, attr, args, confirm=False, agree=False):
		filename = getattr(app.__class__, attr).get_filename(app.get_ini_file())
		if not filename or not os.path.exists(filename):
			return None
		elinks_exists = subprocess.call(['which', 'elinks'], stdout=subprocess.PIPE) == 0
		if not elinks_exists:
			return None
		self._subprocess(['elinks', '-dump', filename], 'readme')
		if not args.noninteractive:
			try:
				if agree:
					aggreed = input('Do you agree [y/N]? ')
					return aggreed.lower()[:1] in ['y', 'j']
				elif confirm:
					input('Press [ENTER] to continue')
					return True
			except (KeyboardInterrupt, EOFError):
				return False
		return True

	def _call_unjoin_script(self, app, args):
		return self._call_join_script(app, args, unjoin=True)

	def _call_join_script(self, app, args, unjoin=False):
		if not args.call_join_scripts:
			return
		other_script = self._get_joinscript_path(app, unjoin=not unjoin)
		any_number_basename = os.path.basename(other_script)
		any_number_basename = '[0-9][0-9]%s' % any_number_basename[2:]
		any_number_scripts = os.path.join(os.path.dirname(other_script), any_number_basename)
		for other_script in glob(any_number_scripts):
			self.log('Uninstalling %s' % other_script)
			os.unlink(other_script)
		if unjoin:
			ext = 'uinst'
		else:
			ext = 'inst'
		joinscript = app.get_cache_file(ext)
		ret = dest = None
		if os.path.exists(joinscript):
			self.log('Installing join script %s' % joinscript)
			dest = self._get_joinscript_path(app, unjoin=unjoin)
			shutil.copy2(joinscript, dest)
			# change to UCS umask + +x:      -rwxr-xr-x
			os.chmod(dest, 0o755)
		if ucr_get('server/role') == 'domaincontroller_master' and getuser() == 'root':
			ret = self._call_script('/usr/sbin/univention-run-join-scripts')
		else:
			with self._get_password_file(args) as password_file:
				if password_file:
					username = self._get_username(args)
					ret = self._call_script('/usr/sbin/univention-run-join-scripts', '-dcaccount', username, '-dcpwd', password_file)
		return ret

	def _get_configure_settings(self, app, filter_action=True):
		set_vars = {}
		phase = self.get_action_name().title()
		for setting in app.get_settings():
			if setting.name in set_vars:
				continue
			if filter_action and phase not in setting.show:
				continue
			try:
				value = setting.get_value(app, phase=phase)
			except SettingValueError:
				value = setting.get_initial_value(app)
			set_vars[setting.name] = value
		return set_vars

	def _update_certificates(self, app, args):
		if not args.update_certificates:
			return
		uc = get_action('update-certificates')
		uc.call(apps=[app])

	def _configure(self, app, args, run_script=None, scope=None):
		if not args.configure:
			return
		if run_script is None:
			run_script = self.get_action_name()
		configure = get_action('configure')
		set_vars = self._get_configure_settings(app)
		if args.set_vars:
			for setting in app.get_settings():
				# we only take those settings from the args
				# that are used for our App
				# => installing two apps at once will sort the
				# settings correctly
				if setting.name in args.set_vars:
					set_vars[setting.name] = args.set_vars[setting.name]
		configure.call(app=app, run_script=run_script, set_vars=set_vars, scope=scope)

	def _reload_apache(self):
		self._call_script('/etc/init.d/apache2', 'reload')

	def dry_run(self, app, args):
		ret = self._dry_run(app, args)
		if ret['install']:
			self.log('The following packages would be INSTALLED/UPGRADED:')
			for pkg in ret['install']:
				self.log(' * %s' % pkg)
		if ret['remove']:
			self.log('The following packages would be REMOVED:')
			for pkg in ret['remove']:
				self.log(' * %s' % pkg)
		if ret['broken']:
			self.log('The following packages are BROKEN:')
			for pkg in ret['broken']:
				self.log(' * %s' % pkg)
		return ret

	def _dry_run(self, app, args):
		raise NotImplementedError()
