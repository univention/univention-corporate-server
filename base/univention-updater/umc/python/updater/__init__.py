#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: updater
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

import re
from os import stat, getpid
from time import time
from hashlib import md5
import subprocess
import psutil
import pipes
import yaml
import requests
from datetime import datetime

import univention.hooks
import notifier.threads

from univention.lib.i18n import Translation
from univention.lib import atjobs
from univention.management.console.log import MODULE
from univention.management.console.config import ucr
from univention.management.console.modules import Base, UMC_Error
from univention.management.console.modules.decorators import simple_response, sanitize
from univention.management.console.modules.sanitizers import ChoicesSanitizer, StringSanitizer, IntegerSanitizer, ListSanitizer

from univention.updater.tools import UniventionUpdater
from univention.updater.errors import RequiredComponentError, UpdaterException

_ = Translation('univention-management-console-module-updater').translate

# the file whose file time is used as the 'serial' value for the 'Components' grid.
COMPONENTS_SERIAL_FILE = '/etc/apt/sources.list.d/20_ucs-online-component.list'

# serial files for the 'Updates' page. Whenever only one of these
# files have changed we have to refresh all elements of the
# 'Updates' page.
UPDATE_SERIAL_FILES = [
	'/etc/apt/mirror.list',
	'/etc/apt/sources.list.d/15_ucs-online-version.list',
	'/etc/apt/sources.list.d/18_ucs-online-errata.list',
	'/etc/apt/sources.list.d/20_ucs-online-component.list'
]

HOOK_DIRECTORY_LEGACY = '/usr/share/pyshared/univention/management/console/modules/updater/hooks'
HOOK_DIRECTORY = '/usr/share/univention-updater/hooks'

INSTALLERS = {
	'release': {
		'purpose': _("Release update to version %s"),
		'command': "/usr/share/univention-updater/univention-updater net --updateto %s --ignoressh --ignoreterm",
		'logfile': '/var/log/univention/updater.log',
		'statusfile': '/var/lib/univention-updater/univention-updater.status',
	},
	'distupgrade': {
		'purpose': _("Package update"),
		'command': "/usr/share/univention-updater/univention-updater-umc-dist-upgrade; /usr/share/univention-updater/univention-updater-check",
		'logfile': '/var/log/univention/updater.log',
		'statusfile': '/var/lib/univention-updater/umc-dist-upgrade.status',
	},
	# This is the call to be invoked when EASY mode is switched on.
	'easyupgrade': {
		'purpose': _("Release update"),
		'command': '/usr/sbin/univention-upgrade --noninteractive --ignoressh --ignoreterm',
		'logfile': '/var/log/univention/updater.log',
		'statusfile': '/var/lib/univention-updater/univention-upgrade.status',
	}
}


class Watched_File(object):

	"""
	A class that takes a file name and watches changes to this file.
	We don't use any advanced technologies (FAM, inotify etc.) but
	rather basic 'stat' calls, monitoring mtime and size.
	"""

	def __init__(self, file, count=2):

		self._file = file
		self._count = count

		self._last_returned_stamp = 0  # the last result we returned to the caller. will be returned as long as there are not enough changes.

		self._unchanged_count = 0  # incremented if size and timestamp didn't change

		self._last_stamp = 0  # last timestamp we've seen
		self._last_size = 0  # last size we've seen
		self._last_md5 = ''

	def timestamp(self):
		"""
		Main function. returns the current timestamp whenever size or mtime
		have changed. Defers returning the new value until changes have
		settled down, e.g. until the same values have appeared 'count' times.
		"""
		current_stamp = 0
		current_size = 0
		st = stat(self._file)
		if st:
			current_stamp = int(st.st_mtime)
			current_size = st.st_size
			# Fake a changed mtime if size is different. Subsequent processing
			# only depends on the mtime field.
			if current_size != self._last_size:
				current_stamp = int(time())
				MODULE.info("Size of '%s': %s -> %s" % (self._file, self._last_size, current_size))
				self._last_size = current_size

		if current_stamp == self._last_stamp:
			self._unchanged_count += 1
			if self._unchanged_count >= self._count:
				# Don't record new timestamp if MD5 of file is the same
				try:
					with open(self._file, 'rb') as fd:
						hash_ = md5(fd.read()).hexdigest()
				except (IOError, OSError):
					pass
				else:
					if hash_ != self._last_md5:
						self._last_md5 = hash_
						self._last_returned_stamp = current_stamp
					else:
						MODULE.info("Hash of '%s' unchanged" % self._file)
		else:
			self._unchanged_count = 0
			self._last_stamp = current_stamp

		return self._last_returned_stamp


class Watched_Files(object):

	""" Convenience class to monitor more than one file at a time.
	"""

	def __init__(self, files, count=2):
		self._count = count
		self._files = []

		self._last_returned_stamp = 0  # the last result we returned to the caller. will be returned as long as there are not enough changes.

		self._unchanged_count = 0  # incremented if size and timestamp didn't change

		self._last_stamp = 0  # last timestamp we've seen

		for f in files:
			self._files.append(Watched_File(f, 0))

	def timestamp(self):
		max = 0
		for f in self._files:
			stamp = f.timestamp()
			if stamp > max:
				max = stamp

		if max == self._last_stamp:
			self._unchanged_count += 1
			if self._unchanged_count >= self._count:
				self._last_returned_stamp = max
		else:
			self._unchanged_count = 0
			self._last_stamp = max

		return self._last_returned_stamp


class Instance(Base):

	def init(self):
		MODULE.info("Initializing 'updater' module (PID = %d)" % (getpid(),))
		self._current_job = ''
		self._logfile_start_line = 0
		self._serial_file = Watched_File(COMPONENTS_SERIAL_FILE)
		self._updates_serial = Watched_Files(UPDATE_SERIAL_FILES)
		try:
			self.uu = UniventionUpdater(False)
		except Exception as exc:  # FIXME: let it raise
			MODULE.error("init() ERROR: %s" % (exc,))

	@simple_response
	def query_maintenance_information(self):
		ret = self._maintenance_information()
		ret.update(self._last_update())
		return ret

	def _last_update(self):
		status_file = '/var/lib/univention-updater/univention-updater.status'
		ret = {'last_update_failed': False, 'last_update_version': None}
		try:
			mtime = stat(status_file).st_mtime
			mtime = datetime.fromtimestamp(mtime)
			delta = datetime.now() - mtime
			if delta.days != 0:  # no fresh failure
				return ret
			with open(status_file) as fd:
				content = fd.read()
				info = dict(line.split('=', 1) for line in content.splitlines())
				ret['last_update_failed'] = info.get('status') == 'FAILED'
				if ret['last_update_failed']:
					ret['last_update_version'] = info.get('next_version')
		except (ValueError, EnvironmentError) as exc:
			MODULE.error(str(exc))
			pass
		return ret

	def _maintenance_information(self):
		ucr.load()
		if ucr.is_true('license/extended_maintenance/disable_warning'):
			return {'show_warning': False}
		version = self.uu.get_ucs_version()
		try:
			url = 'https://updates.software-univention.de/download/ucs-maintenance/{}.yaml'.format(version)
			response = requests.get(url, timeout=10)
			if not response.ok:
				response.raise_for_status()
			status = yaml.safe_load(response.content)
			if not isinstance(status, dict):
				raise yaml.YAMLError(repr(status))
			# the yaml file contains for maintained either false, true or extended as value.
			# yaml.load converts true and false into booleans but extended into string.
			_maintained_status = status.get('maintained')
			maintenance_extended = _maintained_status == 'extended'
			show_warning = maintenance_extended or not _maintained_status
		except yaml.YAMLError as exc:
			MODULE.error('The YAML format is malformed: %s' % (exc,))
			return {'show_warning': False}
		except requests.exceptions.RequestException as exc:
			MODULE.error("Querying maintenance information failed: %s" % (exc,))
			return {'show_warning': False}

		return {
			'ucs_version': version,
			'show_warning': show_warning,
			'maintenance_extended': maintenance_extended,
			'base_dn': ucr.get('license/base')
		}

	@simple_response
	def poll(self):
		return True

	@simple_response
	def query_releases(self):
		"""
		Returns a list of system releases suitable for the
		corresponding ComboBox
		"""

		# be as current as possible.
		self.uu.ucr_reinit()
		ucr.load()

		appliance_mode = ucr.is_true('server/appliance')

		available_versions, blocking_components = self.uu.get_all_available_release_updates()
		result = [{'id': rel, 'label': 'UCS %s' % (rel,)} for rel in available_versions]
		#
		# appliance_mode=no ; blocking_comp=no  → add "latest version"
		# appliance_mode=no ; blocking_comp=yes →  no "latest version"
		# appliance_mode=yes; blocking_comp=no  → add "latest version"
		# appliance_mode=yes; blocking_comp=yes → add "latest version"
		#
		if result and (appliance_mode or not blocking_components):
			# UniventionUpdater returns available version in ascending order, so
			# the last returned entry is the one to be flagged as 'latest' if there's
			# no blocking component.
			result[-1]['label'] = '%s (%s)' % (result[-1]['label'], _('latest version'))

		return result

	@sanitize(
		hooks=ListSanitizer(StringSanitizer(minimum=1), required=True)
	)
	def call_hooks(self, request):
		"""
		Calls the specified hooks and returns data given back by each hook
		"""

		def _thread(request):
			result = {}
			hookmanager_legacy = univention.hooks.HookManager(HOOK_DIRECTORY_LEGACY)  # , raise_exceptions=False
			hookmanager = univention.hooks.HookManager(HOOK_DIRECTORY)  # , raise_exceptions=False

			hooknames = request.options.get('hooks')
			MODULE.info('requested hooks: %s' % hooknames)
			for hookname in hooknames:
				MODULE.info('calling hook %s' % hookname)
				result[hookname] = hookmanager.call_hook(hookname) + hookmanager_legacy.call_hook(hookname)

			MODULE.info('result: %r' % (result,))
			return result

		thread = notifier.threads.Simple('call_hooks', notifier.Callback(_thread, request), notifier.Callback(self.thread_finished_callback, request))
		thread.run()

	@simple_response
	def updates_serial(self):
		"""
		Watches the three `sources.list` snippets for changes
		"""
		result = self._updates_serial.timestamp()
		MODULE.info(" -> Serial for UPDATES is '%s'" % result)
		return result

	@simple_response
	def updates_check(self):
		"""
		Returns the list of packages to be updated/installed
		by a dist-upgrade.
		"""
		p0 = subprocess.Popen(['LC_ALL=C apt-get update'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		(stdout, stderr) = p0.communicate()

		p1 = subprocess.Popen(['LC_ALL=C apt-get -u dist-upgrade -s'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		(stdout, stderr) = p1.communicate()

		install = []
		update = []
		remove = []
		for line in stdout.split('\n'):
			# upgrade:
			#   Inst univention-updater [3.1.1-5] (3.1.1-6.408.200810311159 192.168.0.10)
			# inst:
			#   Inst mc (1:4.6.1-6.12.200710211124 oxae-update.open-xchange.com)
			#
			# *** FIX ***   the above example lines ignore the fact that there's
			#               some extra text (occasionally) after the last closing
			#               parenthesis. Until now, I've seen only a pair of empty
			#               brackets [], but who knows...
			match = re.search(r'^Inst (\S+)\s+(.*?)\s*\((\S+)\s.*\)', line)
			if match:
				pkg = match.group(1)
				old = match.group(2)
				ver = match.group(3)
				if old:
					update.append([pkg, ver])
				else:
					install.append([pkg, ver])
			elif line.startswith('Remv '):
				ll = line.split(' ')
				pkg = ll[1]
				# i18n: The package version is unknown.
				ver = _('unknown')
				if len(ll) > 2:
					ver = ll[2].replace('[', '').replace(']', '')
				remove.append([pkg, ver])

		return dict(
			update=sorted(update),
			install=sorted(install),
			remove=sorted(remove),
		)

	@simple_response
	def updates_available(self):
		"""
		Asks if there are package updates available. (don't get confused
		by the name of the UniventionUpdater function that is called here.)
		This is a separate call since it can take an amount of time, thus
		being invoked by a separate button (and not in the background)
		"""
		ucr.load()
		try:
			# be as current as possible.
			what = 'reinitializing UniventionUpdater'
			self.uu.ucr_reinit()

			what = 'checking update availability'
			return self.uu.component_update_available()
		except Exception as ex:
			typ = str(type(ex)).strip('<>')
			msg = '[while %s] [%s] %s' % (what, typ, str(ex))
			MODULE.error(msg)
		return False

	def status(self, request):  # TODO: remove unneeded things
		"""One call for all single-value variables."""

		result = {}
		ucr.load()

		try:
			result['erratalevel'] = int(ucr.get('version/erratalevel', 0))
		except ValueError:
			result['erratalevel'] = 0

		result['appliance_mode'] = ucr.is_true('server/appliance')
		result['easy_mode'] = ucr.is_true('update/umc/updateprocess/easy', False)
		result['timestamp'] = int(time())
		result['reboot_required'] = ucr.is_true('update/reboot/required', False)

		try:
			# be as current as possible.
			what = 'reinitializing UniventionUpdater'
			self.uu.ucr_reinit()

			what = 'getting UCS version'
			result['ucs_version'] = self.uu.get_ucs_version()

			# if nothing is returned -> convert to empty string.
			what = 'querying available release updates'
			try:
				result['release_update_available'] = self.uu.release_update_available(errorsto='exception')
			except RequiredComponentError as exc:
				result['release_update_available'] = exc.version
			if result['release_update_available'] is None:
				result['release_update_available'] = ''

			what = 'querying update-blocking components'
			try:
				blocking_components = self.uu.get_all_available_release_updates()[1]
			except (UpdaterException, ValueError) as exc:
				msg = _('Error contacting the update server. Please check your proxy or firewall settings, if any. Or it may be a problem with your configured DNS server.')
				msg += ' ' + _('This is the error message:') + ' ' + str(exc)
				raise UMC_Error(msg)
			# check apps
			if result['release_update_available']:
				try:
					from univention.appcenter.actions import get_action
					update_check = get_action('update-check')
					if update_check is not None:
						blocking_apps = update_check.get_blocking_apps(ucs_version=str(result['release_update_available']))
						if blocking_apps:
							blocking_components.update(set(blocking_apps))
				except (ImportError, ValueError):
					# the new univention.appcenter package is not installed.
					# Cannot be a dependency as the app center depends on updater...
					raise UMC_Error(_('Error checking if installed apps are available for next UCS version.'))

			result['release_update_blocking_components'] = ' '.join(blocking_components or [])

			what = "querying availability for easy mode"

			if result['easy_mode']:
				# updates/available should reflect the need for an update
				easy_update_available = ucr.is_true('update/available', False)
				# but don't rely on ucr! update/available is set during univention-upgrade --check
				# but when was the last time this was run?

				# release update
				easy_update_available = easy_update_available or result['release_update_available']
				# if no update seems necessary perform a real (expensive) check nonetheless
				easy_update_available = easy_update_available or self.uu.component_update_available()
				result['easy_update_available'] = bool(easy_update_available)
			else:
				result['easy_update_available'] = False

			# Component counts are now part of the general 'status' data.
			what = "counting components"
			c_count = 0
			e_count = 0
			for comp in self.uu.get_all_components():
				c_count = c_count + 1
				if ucr.is_true('repository/online/component/%s' % (comp,), False):
					e_count = e_count + 1
			result['components'] = c_count
			result['enabled'] = e_count

			# HACK: the 'Updates' form polls on the serial file
			#       to refresh itself. Including the serial value
			#       into the form helps us to have a dependent field
			#       that can trigger the refresh of the "Releases"
			#       combobox and the 'package updates available' field.
			result['serial'] = self._serial_file.timestamp()

		except Exception as exc:  # FIXME: don't catch everything
			msg = _('Error contacting the update server. Please check your proxy or firewall settings, if any. Or it may be a problem with your configured DNS server.')
			msg += ' ' + _('This is the error message:') + ' ' + str(exc)
			raise UMC_Error(msg)

		self.finished(request.id, [result])

	@simple_response
	def reboot(self):
		"""
		Reboots the computer. Simply invokes /sbin/reboot in the background
		and returns success to the caller. The caller is prepared for
		connection loss.
		"""
		subprocess.call(['/sbin/reboot'])
		return True

	@simple_response
	def running(self):
		"""
		Returns the id (key into INSTALLERS) of a currently
		running job, or the empty string if nothing is running.
		"""
		return self.__which_job_is_running()

	@sanitize(
		job=ChoicesSanitizer(INSTALLERS.keys() + [''], required=True),
		count=IntegerSanitizer(default=0),
	)
	@simple_response
	def updater_log_file(self, job, count):
		"""
		returns the content of the log file associated with
		the job.

		:param count: has the same meaning as already known:
			<0 ...... return timestamp of file (for polling)
			0 ....... return whole file as a string list
			>0 ...... ignore this many lines, return the rest of the file

		.. note::
			As soon as we have looked for a running job at least once,
			we know the job key and can associate it here.

		TODO: honor a given 'job' argument
		"""
		job = self._current_job or job

		if not job:
			return

		fname = INSTALLERS[job]['logfile']
		if count < 0:
			try:
				return stat(fname)[9]
			except (IOError, OSError):
				return 0

		# don't read complete file if we have an 'ignore' count
		count += self._logfile_start_line
		return self._logview(fname, -count)

	def _logview(self, fname, count):
		"""
		Contains all functions needed to view or 'tail' an arbitrary text file.

		:param count: can have different values:
			< 0 ... ignore this many lines, return the rest of the file
			0 ..... return the whole file, split into lines.
			> 0 ... return the last 'count' lines of the file. (a.k.a. tail -n <count>)
		"""
		lines = []
		try:
			with open(fname, 'rb') as fd:
				for line in fd:
					if (count < 0):
						count += 1
					else:
						lines.append(line.rstrip().decode('utf-8', 'replace'))
						if (count > 0) and (len(lines) > count):
							lines.pop(0)
		except (IOError, OSError):
			pass
		return lines

	@sanitize(
		job=ChoicesSanitizer(INSTALLERS.keys(), required=True),
	)
	@simple_response
	def updater_job_status(self, job):  # TODO: remove this completely
		"""Returns the status of the current/last update even if the job is not running anymore."""
		result = {}
		try:
			with open(INSTALLERS[job]['statusfile'], 'rb') as fd:
				for line in fd:
					fields = line.strip().split('=')
					if len(fields) == 2:
						result['_%s_' % fields[0]] = fields[1]
		except (IOError, OSError):
			pass

		result['running'] = '' != self.__which_job_is_running()
		return result

	@sanitize(
		job=ChoicesSanitizer(INSTALLERS.keys(), required=True),
		detail=StringSanitizer(r'^[A-Za-z0-9\.\- ]*$'),
	)
	@simple_response
	def run_installer(self, job, detail=''):
		"""
		This is the function that invokes any kind of installer. Arguments accepted:
		job ..... the main thing to do. can be one of:
			'release' ...... perform a release update
			'distupgrade' .. update all currently installed packages (distupgrade)
			'check' ........ check what would be done for 'update' ... do we need this?
		detail ....... an argument that specifies the subject of the installer:
			for 'release' .... the target release number,
			for all other subjects: detail has no meaning.
		"""

		MODULE.info("Starting function %r" % (job,))
		self._current_job = job

		# remember initial lines of logfile before starting update to not show it in the frontend
		logfile = INSTALLERS[job]['logfile']
		try:
			with open(logfile, 'rb') as fd:
				self._logfile_start_line = sum(1 for line in fd)
		except (IOError, OSError):
			pass

		command = INSTALLERS[job]['command']
		if '%' in command:
			command = command % (pipes.quote(detail).replace('\n', '').replace('\r', '').replace('\x00', ''),)

		prejob = '/usr/share/univention-updater/disable-apache2-umc'
		postjob = '/usr/share/univention-updater/enable-apache2-umc --no-restart'
		if job == 'release':
			prejob = 'ucr set updater/maintenance=true'
			postjob = 'ucr set updater/maintenance=false'
		MODULE.info("Creating job: %r" % (command,))
		command = '''
%s
%s < /dev/null
%s''' % (prejob, command, postjob)
		atjobs.add(command, comments=dict(lines=self._logfile_start_line))

		return {'status': 0}

	def __which_job_is_running(self):
		# first check running at jobs
		for atjob in atjobs.list(True):
			for job, inst in INSTALLERS.iteritems():
				cmd = inst['command'].split('%')[0]
				if cmd in atjob.command:
					self._current_job = job
					try:
						self._logfile_start_line = int(atjob.comments.get('lines', 0))
					except ValueError:
						pass
					return job
		# no atjob found, parse process list (if univention-upgrade was started via CLI)
		commands = [
			('/usr/share/univention-updater/univention-updater-umc-dist-upgrade', 'distupgrade'),
			('/usr/share/univention-updater/univention-updater', 'release'),
			('/usr/sbin/univention-upgrade', 'distupgrade')  # we don't know if it is a dist-upgrade or a release upgrade
		]
		for cmd, job in commands:
			for process in psutil.process_iter():
				try:
					cmdline = process.cmdline() if callable(process.cmdline) else process.cmdline
				except psutil.NoSuchProcess:
					pass

				if cmd in cmdline:
					self._current_job = job
					self._logfile_start_line = 0
					return job
		return ''
