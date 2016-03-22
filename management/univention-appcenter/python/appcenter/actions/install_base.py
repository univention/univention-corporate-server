#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app base module for installing, uninstalling, upgrading an app
#
# Copyright 2015-2016 Univention GmbH
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
from getpass import getuser
import subprocess
from argparse import SUPPRESS
from tempfile import NamedTemporaryFile

from univention.appcenter.app import App, AppManager
from univention.appcenter.actions import Abort, StoreAppAction, NetworkError, get_action
from univention.appcenter.actions.register import Register
from univention.appcenter.utils import get_locale
from univention.appcenter.ucr import ucr_get


class _AptLogger(object):
	def __init__(self, action, end):
		import re
		self.action = action
		self.progress_re = re.compile('^pmstatus:[^:]+:((\d+\.)?\d+):.*$')
		self.download_re = re.compile('^dlstatus:[^:]+:((\d+\.)?\d+):.*$')
		self.start = self.action.percentage
		self.end = end

	def debug(self, msg):
		self.action.debug(msg)

	def info(self, msg):
		match = self.progress_re.match(msg)
		if match:
			if self.end:
				percentage = float(match.groups()[0]) / 100
				percentage = self.start + ((self.end - self.start) * percentage)
				self.action.percentage = percentage
		elif self.download_re.match(msg):
			pass
		else:
			self.action.log(msg)

	def warn(self, msg):
		self.action.warn(msg)


class InstallRemoveUpgrade(Register):
	prescript_ext = None
	pre_readme = None
	post_readme = None

	def setup_parser(self, parser):
		super(Register, self).setup_parser(parser)
		parser.add_argument('--skip-checks', nargs='*', choices=[req.name for req in App._requirements if self.get_action_name() in req.actions], help=SUPPRESS)
		parser.add_argument('--do-not-send-info', action='store_false', dest='send_info', help=SUPPRESS)
		parser.add_argument('app', action=StoreAppAction, help='The ID of the application')

	main = None  # no action by itself

	def do_it(self, args):
		app = args.app
		status = 200
		try:
			action = self.get_action_name()
			self.log('Going to %s %s (%s)' % (action, app.name, app.version))
			errors, warnings = app.check(action)
			can_continue = self._handle_errors(app, args, errors, True)
			can_continue = self._handle_errors(app, args, warnings, False) and can_continue
			if not can_continue or not self._call_prescript(app):
				status = 0
				self.fatal('Unable to %s %s. Aborting...' % (action, app.id))
			else:
				try:
					self._show_license(app, args)
					self._show_pre_readme(app, args)
					try:
						self._do_it(app, args)
					except (Abort, KeyboardInterrupt) as exc:
						msg = str(exc)
						if msg:
							self.warn(msg)
						self.warn('Aborting...')
						status = 401
					except Exception:
						status = 500
						raise
					else:
						try:
							self._show_post_readme(app, args)
						except Abort:
							pass
				except Abort:
					self.warn('Cancelled...')
					status = 0
		except Exception:
			raise
		else:
			return status == 200
		finally:
			if status == 0:
				pass
			else:
				if status != 200:
					self._revert(app, args)
				if args.send_info:
					try:
						self._send_information(app, status)
					except NetworkError:
						self.log('Ignoring this error...')
				self._register_installed_apps_in_ucr()
				upgrade_search = get_action('upgrade-search')
				upgrade_search.call(app=[app])

	def _handle_errors(self, app, args, errors, fatal):
		can_continue = True
		for error in errors:
			details = errors[error]
			try:
				requirement = [req for req in app._requirements if req.name == error][0]
				try:
					message = requirement.func.__doc__ % details
				except TypeError:
					message = requirement.func.__doc__
			except IndexError:
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
					aggreed = raw_input('Do you want to %s anyway [y/N]? ' % self.get_action_name())
				except (KeyboardInterrupt, EOFError):
					return False
				else:
					return aggreed.lower()[:1] in ['y', 'j']
		return True

	def _call_prescript(self, app, **kwargs):
		ext = self.prescript_ext
		self.debug('Calling prescript (%s)' % ext)
		if not ext:
			return True
		with NamedTemporaryFile('r+b') as error_file:
			kwargs['version'] = app.version
			kwargs['error_file'] = error_file.name
			locale = get_locale()
			if locale:
				kwargs['locale'] = locale
			success = self._call_cache_script(app, ext, **kwargs)
			if success is None:
				# no prescript
				success = True
			if not success:
				for line in error_file:
					self.warn(line)
			return success

	def _revert(self, app, args):
		pass

	def _do_it(self, app, args):
		raise NotImplementedError()

	def _show_license(self, app, args):
		if self._show_file(app, 'license_agreement', args, agree=True) is False:
			raise Abort()

	def _show_pre_readme(self, app, args):
		if self._show_file(app, self.pre_readme, args, confirm=True) is False:
			raise Abort()

	def _show_post_readme(self, app, args):
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
					aggreed = raw_input('Do you agree [y/N]? ')
					return aggreed.lower()[:1] in ['y', 'j']
				elif confirm:
					raw_input('Press [ENTER] to continue')
					return True
			except (KeyboardInterrupt, EOFError):
				return False
		return True

	def _call_unjoin_script(self, app, args):
		return self._call_join_script(app, args, unjoin=True)

	def _call_join_script(self, app, args, unjoin=False):
		other_script = self._get_joinscript_path(app, unjoin=not unjoin)
		if os.path.exists(other_script):
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
			os.chmod(dest, 0755)
			if ucr_get('server/role') == 'domaincontroller_master' and getuser() == 'root':
				ret = self._call_script(dest)
			else:
				with self._get_password_file(args) as password_file:
					joinargs = []
					if password_file:
						joinargs.extend(['-dcname', self._get_username(args)])
						joinargs.extend(['-dcpwd', password_file])
					ret = self._call_script(dest, *joinargs)
		if ret is True and dest and unjoin:
			os.unlink(dest)
		return ret

	def _reload_apache(self):
		self._call_script('/etc/init.d/apache2', 'reload')

	def _apt_get_update(self):
		self._subprocess(['/usr/bin/apt-get', 'update'])
		AppManager.reload_package_manager()

	def _apt_get(self, command, packages, percentage_end=100, update=True):
		env = os.environ.copy()
		env['DEBIAN_FRONTEND'] = 'noninteractive'
		if update:
			self._apt_get_update()
		apt_logger = _AptLogger(self, percentage_end)
		try:
			return self._subprocess(['/usr/bin/apt-get', '-o', 'APT::Status-Fd=1', '-o', 'DPkg::Options::=--force-confold', '--assume-yes', '--force-yes', '--auto-remove', command] + packages, logger=apt_logger, env=env)
		finally:
			AppManager.reload_package_manager()
