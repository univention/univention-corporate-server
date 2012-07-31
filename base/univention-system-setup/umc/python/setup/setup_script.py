#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention System Setup
#  software installation script
#
# Copyright 2012 Univention GmbH
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
import sys
import re

import univention.config_registry
from util import PATH_SETUP_SCRIPTS, PATH_PROFILE
# FIXME: This should be done in util.py!!
if not PATH_SETUP_SCRIPTS.endswith('/'):
	PATH_SETUP_SCRIPTS += '/'
ucr = univention.config_registry.ConfigRegistry()

from univention.lib.i18n import Translation
_ = Translation('univention-system-setup-scripts').translate

class SetupScript(object):
	'''Baseclass for all Python-based Setup-Scripts.

	Script lifecycle:
	  __init__() -> up()
	  run() -> inner_run() -> down()

	up(), inner_run(), and down() and encapsulated by try-blocks,
	so the script should under no cirucumstances break.

	You should define name and script_name class (or instance) variables
	where name is localised and will show up at top of the progress and
	script_name is for logging and internal infos found at
	univention.management.console.modules.setup.util.ProgressParser.FRACTIONS
	You probably want to set script_name to os.path.abspath(__file__)

	You should define your own inner_run-method, and, if needed,
	override (initially dummy) up() and down()

	You should execute a script like so:
	script = MySetupScript()
	script.run()
	Or maybe even better like so, as it calls sys.exit
	if __name__ == '__main__':
		script = MySetupScript()
		main(script) # helper function defined in here

	You may control the progress parser with these methods:
	self.header(msg) # automatically called by run()
	self.message(msg)
	self.error(msg)
	self.join_error(msg)
	self.steps(steps)
	self.step(step)
	'''
	name = ''

	# you almost definitely want to assign os.path.abspath(__file__)
	script_name = '' 

	def __init__(self, *args, **kwargs):
		'''Initialise Script. Will call self.up() with same *args
		and **kwargs as __init__() (which itself will leave them
		untouched)

		So dont override this method, instead write your own up().
		The default up()-method does nothing.

		self.up() is called in a try-except-block. If an exception
		was raised by up(), it will be saved and raised as soon as
		run() is called. You should make sure that this does not
		happen.
		'''
		# get a fresh ucr in every script
		ucr.load()
		self._step = 1
		# remove script path from name
		if self.script_name:
			if self.script_name.startswith(PATH_SETUP_SCRIPTS):
				self.script_name = self.script_name[len(PATH_SETUP_SCRIPTS):]
		try:
			self.up(*args, **kwargs)
		except Exception as e:
			# save caught exception. raise later (in run())
			self._broken = e
		else:
			self._broken = False

	def inform_progress_parser(self, progress_attribute, msg):
		'''Internal method to inform progress parser.

		At the moment it writes info in a file which will be
		read by the parser. In a more advanced version, the script
		could change the state of the progress directly.
		'''
		msg = '__%s__:%s' % (progress_attribute.upper(), msg)
		if not msg.endswith('\n'):
			msg += '\n'
		sys.stdout.write(msg)
		sys.stdout.flush()

	def header(self, msg):
		'''Write header info of this script.

		Called automatically by run(). Probably unneeded by developers
		'''
		self.inform_progress_parser('name', '%s %s' % (self.script_name, msg))

	def message(self, msg):
		'''Write a harmless __MSG__: for the parser
		'''
		self.inform_progress_parser('msg', msg)

	def error(self, msg):
		'''Write a non-critical __ERR__: for the parser
		The parser will save the error and inform the frontend
		that something went wrong
		'''
		self.inform_progress_parser('err', msg)

	def join_error(self, msg):
		'''Write a critical __JOINERR__: for the parser.
		The parser will save it and inform the frontend that something
		went terribly wrong leaving the system in an unjoined state
		'''
		self.inform_progress_parser('joinerr', msg)

	def steps(self, steps):
		'''Total number of __STEPS__: to come throughout the whole
		script. Progress within the script should be done with
		step() which is relative to steps()
		'''
		self.inform_progress_parser('steps', steps)

	def step(self, step=None):
		'''Inform parser that the next __STEP__: in this script
		was done. You can provide an exact number or None
		in which case an internal counter will be incremented
		'''
		if step is not None:
			self._step = step
		self.inform_progress_parser('step', self._step)
		self._step += 1

	def log(self, *msgs):
		'''Log messages in a log file'''
		print '### LOG ###'
		for msg in msgs:
			print msg,
		print

	def set_ucr_var(self, var_name, value):
		'''Set the value of var_name of ucr.
		Saves immediately'''
		ucr[var_name] = value
		ucr.save()

	def get_ucr_var(self, var_name):
		'''Retrieve the value of var_name from ucr'''
		return ucr.get(var_name)

	def get_profile_var(self, var_name, default=''):
		'''Retrieve the value of var_name from the profile file.
		If not found, return default.
		'''
		if not hasattr(self, '_profile_vars'):
			self._profile_vars = {}
			with open(PATH_PROFILE) as f:
				for line in f.readlines():
					match = re.match(r'^(.+)="(.*)"\n$', line)
					if match:
						self._profile_vars[match.groups()[0]] = match.groups()[1]
		return self._profile_vars.get(var_name, default)

	def get_profile_var_list(self, var_name, split_by=' '):
		'''Retrieve the value of var_name from the profile file.
		Return the string as a list split by split_by.
		'''
		val = self.get_profile_var(var_name)
		if not val:
			return []
		else:
			return val.split(split_by)

	def run(self):
		'''Run the SetupScript.
		Dont override this method, instead define your own
		inner_run()-method.

		Call self.header()
		If up() failed raise its exception.
		Run inner_run() in a try-except-block
		Return False if an exception occurred
		Otherwise return True/False depending on
		return code of inner_run itself.
		*In any case*, run self.down() in a try-except-block
		afterwards. If this should fail, return False.
		'''
		if self.name:
			self.header(self.name)
		try:
			if self._broken:
				raise self._broken
			else:
				success = self.inner_run()
		except Exception as e:
			self.error(str(e))
			success = False
		finally:
			try:
				self.down()
			except:
				success = False
		return success is not False

	def inner_run(self):
		'''Main function, called by run().
		Override this method in your SetupScriptClass.
		You may return True or False which will be propagated
		to run() itself. If you dont return False, True will be
		used implicitely.
		'''
		raise NotImplementedError('Define you own inner_run() method, please.')

	def up(self, *args, **kwargs):
		'''Override this method if needed.
		It is called during __init__ with the very same parameters
		as __init__ was called.
		'''
		pass

	def down(self):
		'''Override this method if needed.
		It is called at the end of run() even when an error in up()
		or inner_run() occurred.
		'''
		pass

import os
import apt_pkg
import apt
import apt.progress
from apt.cache import FetchFailedException, LockFailedException

class MessageWriter(object):
	'''Mimics a file object (default: stdout)
	supports flush and write. Writes no '\\r',
	writes no empty strings, writes not just spaces.
	If it writes its tweaking output: '__MSG__:%s\\n' '''

	def __init__(self, file_object=None):
		if file_object is None:
			file_object = sys.stdout
		self.file_object = file_object

	def flush(self):
		self.file_object.flush()

	def write(self, msg):
		msg = msg.replace('\r', '').strip()
		if msg:
			self.file_object.write('__MSG__:%s\n' % msg)

class FetchProgress(apt.progress.text.AcquireProgress):
	'''Used to handle information about fetching packages.
	Writes a lot of __MSG__es, as it uses MessageWriter
	'''
	def __init__(self, outfile=None):
		super(FetchProgress, self).__init__()
		self._file = MessageWriter()

	# dont use _winch
	def start(self):
		super(apt.progress.text.AcquireProgress, self).start()
		import signal
		self._signal = signal.SIG_IGN

	# force defaults
	def _write(self, msg, newline=True, maximize=True):
		super(FetchProgress, self)._write(msg, newline=False, maximize=False)

class DpkgProgress(apt.progress.base.InstallProgress):
	'''Progress when installing or removing software.
	Writes messages (and percentage) from apts status file descriptor
	'''
	def __init__(self, script):
		super(DpkgProgress, self).__init__()
		self.script = script

	# status == pmstatus
	def status_change(self, pkg, percent, status):
		self.script.message('%s' % (status))
		self.script.step(self.script.tasks_finished * 100 + int(percent))

	# status == pmerror
	def error(self, pkg, errormsg):
		self.script.log('ERROR!! %s: %s' % (pkg, errormsg))

#	def start_update(self):
#		self.script.log('SUPDATE')
#
#	def finish_update(self):
#		self.script.log('FUPDATE')
#
#	def conffile(self, current, new):
#		self.script.log('CONFF', current, new)
#
#	def dpkg_status_change(self, pkg, status):
#		self.script.log('DPKG', pkg, status)
#
#	def processing(self, pkg, stage):
#		self.script.log('PROCESS', pkg, status)
#

class AptScript(SetupScript):
	brutal_apt_options = True

	def up(self, *args, **kwargs):
		apt_pkg.init()

		self.always_install = []
		self.tasks_finished = 0
		self.roles_package_map = {
			'domaincontroller_master' : 'univention-server-master',
			'domaincontroller_backup' : 'univention-server-backup',
			'domaincontroller_slave' : 'univention-server-slave',
			'memberserver' : 'univention-server-member',
			'fatclient' : 'univention-managed-client',
			'mobileclient' : 'univention-mobile-client',
		}
		self.current_server_role = self.get_ucr_var('server/role')
		self.wanted_server_role = self.get_profile_var('server/role')

		# dont ever ask for user input (as there is no user...)
		os.environ['DEBIAN_FRONTEND'] = 'noninteractive'
		apt_pkg.config['APT::Get::Assume-Yes'] = 'true'
		apt_pkg.config['APT::Get::force-yes'] = 'true'
		apt_pkg.config['APT::Get::AllowUnauthenticated'] = '1'
		apt_pkg.config['DPkg::Options::'] = '--force-confold'

		# advanced options
		if self.brutal_apt_options:
			apt_pkg.config['DPkg::Options::'] = '--force-overwrite'
			apt_pkg.config['DPkg::Options::'] = '--force-overwrite-dir'
			apt_pkg.config['APT::Get::Trivial-Only'] = 'no'
			apt_pkg.config['quiet'] = '1'

		# initialise the cache as well as progress objects
		self.cache = apt.Cache()
		self.fetch_progress = FetchProgress(sys.stdout)
		self.dpkg_progress = DpkgProgress(self)
	
	def update(self):
		'''apt-get update
		Returns success
		'''
		try:
			self.cache.update(self.fetch_progress)
		except FetchFailedException:
			self.error(_('Fetch failed'))
			return False
		except LockFailedException:
			self.error(_('Failed to lock'))
			return False
		else:
			return True

	def get_package(self, pkg_name):
		'''Get Package-object for package_name
		Otherwise write an error
		'''
		try:
			return self.cache[pkg_name]
		except KeyError:
			self.error('%s: %s' % (pkg_name, _('No such package')))

	def finish_task(self, *log_msgs):
		'''Task is finished. Increment counter and inform
		the progress parser. Reopen the cache (maybe unneeded
		but does not slow us down too much).
		'''
		# dont log msgs for now
		self.tasks_finished += 1
		self.step(self.tasks_finished * 100)
		self.cache.open()

	def commit(self, install=None, remove=None, msg_if_failed=''):
		'''Really commit changes (mark_install or mark_delete)
		or pass Package-objects that shall be commited.
		Never forgets to pass progress objects, may print error
		messages, always reopens cache.
		'''
		if install is None:
			install = []
		if remove is None:
			remove = []
		for pkg in install:
			pkg.mark_install()
		for pkg in remove:
			pkg.mark_delete()
		try:
			result = self.cache.commit(fetch_progress=self.fetch_progress, install_progress=self.dpkg_progress)
			if not result:
				raise SystemError()
		except SystemError:
			if msg_if_failed:
				self.error(msg_if_failed)
		# better do a:
		self.cache.open()

	def install(self, *pkg_names):
		'''Instantly installs packages when found'''
		pkgs = []
		for pkg_name in pkg_names:
			pkg = self.get_package(pkg_name)
			if pkg is not None:
				pkgs.append(pkg)
		self.commit(install=pkgs)
		for pkg in pkgs:
			if not pkg.is_installed:
				self.error('%s: %s' % (pkg.name, _('Failed to install')))

	def uninstall(self, *pkg_names):
		'''Instantly deletes packages when found'''
		pkgs = []
		for pkg_name in pkg_names:
			pkg = self.get_package(pkg_name)
			if pkg is not None:
				pkgs.append(pkg)
		self.commit(install=self.always_install, remove=pkgs)
		for pkg in pkgs:
			if pkg.is_installed:
				self.error('%s: %s' % (pkg.name, _('Failed to uninstall')))

	def get_package_for_role(self, role_name):
		'''Searches for the meta-package that belongs
		to the given role_name
		'''
		try:
			# get "real" package for server/role
			pkg_name = self.roles_package_map[role_name]
			return self.cache[pkg_name]
		except KeyError:
			self.error(_('Failed to get package for Role %s') % role_name)
			return False

	def autoremove(self):
		'''It seems that there is nothing like
		self.cache.autoremove
		So, we need to implement it by hand
		acts as apt-get autoremove
		'''
		for pkg_name in self.cache.keys():
			pkg = self.cache[pkg_name]
			if pkg.is_auto_removable:
				self.message(_('Deleting unneeded %s') % pkg.name)
				pkg.mark_delete()
		if self.cache.get_changes():
			self.commit(msg_if_failed=_('Autoremove failed'))

def main(setup_script, exit=True):
	'''Helper function to run the setup_script and evaluate its
	return code as a "shell-compatible" one. You may sys.exit immediately
	'''
	success = setup_script.run()
	ret_code = 1 - int(success)
	if exit:
		sys.exit(ret_code)
	else:
		return ret_code

