#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: updater
#
# Copyright 2011-2014 Univention GmbH
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

import traceback
import pprint
import subprocess
import univention.management.console as umc
import univention.management.console.modules as umcm
import univention.config_registry

import re
from os import stat, getpid
from time import time
from subprocess import Popen
from hashlib import md5
from copy import deepcopy
import univention.hooks
import notifier.threads

from univention.management.console.log import MODULE
from univention.management.console.modules.decorators import simple_response
from univention.management.console.protocol.definitions import SUCCESS, MODULE_ERR

from univention.updater import UniventionUpdater

_ = umc.Translation('univention-management-console-module-updater').translate

# Base UCR path definitions
ONLINE_BASE	= 'repository/online'
COMPONENT_BASE	= '%s/component' % ONLINE_BASE

# Parameter names for component definitions
COMP_PARTS	= ['maintained','unmaintained']
COMP_PARAMS	= ['description','server','prefix','password','username','defaultpackages','version']

# the file whose file time is used as the 'serial' value for the 'Components' grid.
COMPONENTS_SERIAL_FILE	= '/etc/apt/sources.list.d/20_ucs-online-component.list'

# serial files for the 'Updates' page. Whenever only one of these
# files have changed we have to refresh all elements of the
# 'Updates' page.
UPDATE_SERIAL_FILES = [
	'/etc/apt/mirror.list',
	'/etc/apt/sources.list.d/15_ucs-online-version.list',
	'/etc/apt/sources.list.d/18_ucs-online-errata.list',
	'/etc/apt/sources.list.d/20_ucs-online-component.list'
]

HOOK_DIRECTORY = '/usr/share/pyshared/univention/management/console/modules/updater/hooks'

# Symbolic error codes for UCR write operations
PUT_SUCCESS		= 0
PUT_PARAMETER_ERROR	= 1				# content of request record isn't valid
PUT_PROCESSING_ERROR	= 2				# some error while parameter processing
PUT_WRITE_ERROR		= 3				# some error while saving data
PUT_UPDATER_ERROR	= 4				# after saving options, any errors related to repositories
PUT_UPDATER_NOREPOS	= 5				# nothing committed, but not found any valid repository

# Status codes for the 'execute' function
RUN_SUCCESS		= 0
RUN_PARAMETER_ERROR	= 1
RUN_PROCESSING_ERROR	= 2

INSTALLERS = {
	'release': {
		'purpose':	_("Release update to version %s"),
		'command':	"/usr/share/univention-updater/univention-updater net --updateto %s --ignoressh --ignoreterm",
		'logfile':	'/var/log/univention/updater.log',
		'statusfile':	'/var/lib/univention-updater/univention-updater.status',
	},
	'distupgrade': {
		'purpose':	_("Package update"),
		'command':	"/usr/share/univention-updater/univention-updater-umc-dist-upgrade; /usr/share/univention-updater/univention-updater-check",
		'logfile':	'/var/log/univention/updater.log',
		'statusfile':	'/var/lib/univention-updater/umc-dist-upgrade.status',
	},
	# This is the call to be invoked when EASY mode is switched on.
	'easyupgrade': {
		'purpose':	_("Release update"),
		'command':	'/usr/sbin/univention-upgrade --noninteractive --ignoressh --ignoreterm',
		'logfile':	'/var/log/univention/updater.log',
		'statusfile':	'/var/lib/univention-updater/univention-upgrade.status',
	}
}

class Watched_File(object):
	"""	A class that takes a file name and watches changes to this file.
		We don't use any advanced technologies (FAM, inotify etc.) but
		rather basic 'stat' calls, monitoring mtime and size.
	"""

	def __init__(self,file,count=2):

		self._file = file
		self._count = count

		self._last_returned_stamp = 0	# the last result we returned to the caller. will be
						# returned as long as there are not enough changes.

		self._unchanged_count = 0	# incremented if size and timestamp didn't change

		self._last_stamp = 0		# last timestamp we've seen
		self._last_size = 0		# last size we've seen
		self._last_md5 = ''

	def timestamp(self):
		""" Main function. returns the current timestamp whenever size or mtime
			have changed. Defers returning the new value until changes have
			settled down, e.g. until the same values have appeared 'count' times.
		"""
		current_stamp = 0
		current_size = 0
		try:
			st = stat(self._file)
			if st:
				current_stamp = int(st.st_mtime)
				current_size = st.st_size
				# Fake a changed mtime if size is different. Subsequent processing
				# only depends on the mtime field.
				if current_size != self._last_size:
					current_stamp = int(time())
					MODULE.info("Size of '%s': %s -> %s" % (self._file,self._last_size,current_size))
					self._last_size = current_size
		finally:
			pass

		if current_stamp == self._last_stamp:
			self._unchanged_count += 1
			if self._unchanged_count >= self._count:
				# Don't record new timestamp if MD5 of file is the same
				hash = md5(open(self._file).read()).hexdigest()
				if hash != self._last_md5:
					self._last_md5 = hash
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

	def __init__(self,files,count=2):

		self._count = count
		self._files = []


		self._last_returned_stamp = 0		# the last result we returned to the caller. will be returned
											# as long as there are not enough changes.

		self._unchanged_count = 0			# incremented if size and timestamp didn't change

		self._last_stamp = 0				# last timestamp we've seen

		for f in files:
			self._files.append(Watched_File(f,0))

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

class Instance(umcm.Base):
	def __init__( self ):
		umcm.Base.__init__( self )

		self.init_called = False

	def init(self):
		try:
			if self.init_called:
				MODULE.warn("init() called multiple times!")
				return
			self.init_called = True
			MODULE.info("Initializing 'updater' module (PID = %d, LANG = '%s')" % (getpid(),self.locale))

			self.uu = UniventionUpdater(False)
			self.ucr = univention.config_registry.ConfigRegistry()
			self.ucr.load()

			self._changes = {}	# collects changed UCR vars, for committing the corresponding files
			self._current_job = {}	# remembers last seen status of an installer job

			self._serial_file = Watched_File(COMPONENTS_SERIAL_FILE)
			self._updates_serial = Watched_Files(UPDATE_SERIAL_FILES)

		except Exception, ex:
			MODULE.error("init() ERROR: %s" % str(ex))

	@simple_response
	def poll(self):
		return True

	def query_releases(self,request):
		""" Returns a list of system releases suitable for the
			corresponding ComboBox
		"""

		# ----------- DEBUG -----------------
		MODULE.info("updater/updates/query invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
				MODULE.info("   << %s" % s)
		# -----------------------------------

		# be as current as possible.
		self.uu.ucr_reinit()
		self.ucr.load()

		appliance_mode = self.ucr.is_true('server/appliance')

		result = []
		try:
			request.status = SUCCESS
			available_versions, blocking_components = self.uu.get_all_available_release_updates()
			for rel in available_versions:
				entry = {}
				entry['id'] = rel
				entry['label'] = 'UCS %s' % rel
				result.append(entry)
			#
			# appliance_mode=no ; blocking_comp=no  → add "latest version"
			# appliance_mode=no ; blocking_comp=yes →  no "latest version"
			# appliance_mode=yes; blocking_comp=no  → add "latest version"
			# appliance_mode=yes; blocking_comp=yes → add "latest version"
			#
			if len(result) and (appliance_mode or not blocking_components):
				# UniventionUpdater returns available version in ascending order, so
				# the last returned entry is the one to be flagged as 'latest' if there's
				# no blocking component.
				result[-1]['label'] = '%s (%s)' % (result[-1]['label'],_('latest version'))

		except Exception,ex:
			request.status = MODULE_ERR
			self.finished(request.id, [], str(ex))
			return

		# ----------- DEBUG -----------------
		MODULE.info("updater/updates/query returns: %d entries" % len(result))
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
				MODULE.info("   >> %s" % s)
		# -----------------------------------

		self.finished(request.id,result)

	def _check_thread_error( self, thread, result, request ):
		"""Checks if the thread returned an exception. In that case in
		error response is send and the function returns True. Otherwise
		False is returned."""
		if not isinstance( result, BaseException ):
			return False

		msg = '%s\n%s: %s\n' % ( ''.join( traceback.format_tb( thread.exc_info[ 2 ] ) ), thread.exc_info[ 0 ].__name__, str( thread.exc_info[ 1 ] ) )
		MODULE.process( 'An internal error occurred: %s' % msg )
		self.finished( request.id, None, msg, False )
		return True


	def _thread_finished( self, thread, result, request ):
		if self._check_thread_error( thread, result, request ):
			return
		self.finished( request.id, result )


	def call_hooks(self, request):
		""" Calls the specified hooks and returns data given back by each hook
		"""

		def _thread( request ):
			result = {}

			hookmanager = univention.hooks.HookManager(HOOK_DIRECTORY) # , raise_exceptions=False

			hooknames = request.options.get( 'hooks' )
			MODULE.info('requested hooks: %s' % hooknames)
			for hookname in hooknames:
				MODULE.info('calling hook %s' % hookname)
				result[hookname] = hookmanager.call_hook(hookname)
			MODULE.info('result: %s' % result)

			self.finished(request.id,result)

		thread = notifier.threads.Simple( 'call_hooks', notifier.Callback( _thread, request ),
										  notifier.Callback( self._thread_finished, request ) )
		thread.run()


	def updates_serial(self,request):
		""" Watches the three sources.list snippets for changes
		"""
		result = self._updates_serial.timestamp()
		MODULE.info(" -> Serial for UPDATES is '%s'" % result)
		self.finished(request.id,result)

	def updates_check(self,request):
		"""	Returns the list of packages to be updated/installed
			by a distupgrade.

			*** NOTE *** contrary to the 2.4 behaviour, this call
						does not regenerate the 20....components.list
						since this must have been done recently by
						the 'check for update availability' call.
		"""
		p0 = subprocess.Popen(['LC_ALL=C apt-get update'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		(stdout,stderr) = p0.communicate()

		p1 = subprocess.Popen(['LC_ALL=C apt-get -u dist-upgrade -s'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		(stdout,stderr) = p1.communicate()

		result = {}
		result['install'] = []
		result['update'] = []
		result['remove'] = []
		for line in stdout.split('\n'):
			# upgrade:
			#   Inst univention-updater [3.1.1-5] (3.1.1-6.408.200810311159 192.168.0.10)
			# inst:
			#   Inst mc (1:4.6.1-6.12.200710211124 oxae-update.open-xchange.com)
			#
			# *** FIX ***	the above example lines ignore the fact that there's
			#				some extra text (occasionally) after the last closing
			#				parenthesis. Until now, I've seen only a pair of empty
			#				brackets [], but who knows...
			match = re.search('^Inst (\S+)\s+(.*?)\s*\((\S+)\s.*\)',line)
			if match:
				pkg = match.group(1)
				old = match.group(2)
				ver = match.group(3)
				if old:
					result['update'].append([pkg,ver])
				else:
					result['install'].append([pkg,ver])
			elif line.startswith('Remv '):
				l=line.split(' ')
				pkg = l[1]
				ver = _('unknown')
				if len(l) > 2:
					ver = l[2].replace('[','').replace(']','')
				result['remove'].append([pkg,ver])


		# sort package names?
		result['update'] = sorted(result['update'])
		result['install'] = sorted(result['install'])
		result['remove'] = sorted(result['remove'])

		self.finished(request.id,result)


	def updates_available(self,request):
		""" Asks if there are package updates available. (don't get confused
			by the name of the UniventionUpdater function that is called here.)
			This is a seperate call since it can take an amount of time, thus
			being invoked by a seperate button (and not in the background)
		"""
		# ----------- DEBUG -----------------
		MODULE.info("updater/updates/available invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
				MODULE.info("   << %s" % s)
		# -----------------------------------
		result = False
		what = 'starting'
		try:
			# be as current as possible.
			what = 'reinitializing UniventionUpdater'
			self.uu.ucr_reinit()
			what = 'reloading registry'
			self.ucr.load()

			what = 'checking update availability'
			result = self.uu.component_update_available()

		except Exception, ex:
			typ = str(type(ex)).strip('<>')
			msg = '[while %s] [%s] %s' % (what,typ,str(ex))
			# result['message'] = msg
			# result['status'] = 1
			MODULE.error(msg)

		# ----------- DEBUG -----------------
		MODULE.info("updater/updates/available returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
				MODULE.info("   >> %s" % s)
		# -----------------------------------

		request.status = SUCCESS
		self.finished(request.id,result)

	def status(self,request):
		"""One call for all single-value variables."""
		# ----------- DEBUG -----------------
		MODULE.info("updater/status invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
				MODULE.info("   << %s" % s)
		# -----------------------------------

		response = []
		try:
			result = {}

			# be as current as possible.
			what = 'reinitializing UniventionUpdater'
			self.uu.ucr_reinit()

			what = 'reloading registry'
			self.ucr.load()

			what = 'getting UCS version'
			result['ucs_version'] = self.uu.get_ucs_version()

			# if nothing is returned -> convert to empty string.
			what = 'querying available release updates'
			result['release_update_available'] = self.uu.release_update_available()
			if result['release_update_available'] is None:
				result['release_update_available'] = ''

			what = 'querying update-blocking components'
			blocking_components = self.uu.get_all_available_release_updates()[1]
			if not blocking_components:
				blocking_components = []
			result['release_update_blocking_components'] = list(blocking_components)

			what = 'querying appliance mode'
			result['appliance_mode'] = self.ucr.is_true('server/appliance')

			# current errata patchlevel, converted to int, 0 if unset.
			what = 'querying errata patchlevel'
			result['erratalevel'] = 0
			tmp = self.ucr.get('version/erratalevel')
			if tmp:
				result['erratalevel'] = int(tmp)

			what = "querying availability for easy mode"
			result['easy_mode'] = self.ucr.is_true('update/umc/updateprocess/easy', False)

			if result['easy_mode']:
				# updates/available should reflect the need for an update
				easy_update_available = self.ucr.is_true('update/available', False)
				# but dont rely on ucr! update/available is set during univention-upgrade --check
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
				c_count = c_count+1
				if self.ucr.is_true('%s/%s' % (COMPONENT_BASE,comp),False):
					e_count = e_count+1
			result['components'] = c_count
			result['enabled'] = e_count

			# HACK: the 'Updates' form polls on the serial file
			#		to refresh itself. Including the serial value
			#		into the form helps us to have a dependent field
			#		that can trigger the refresh of the "Releases"
			#		combobox and the 'package updates available' field.
			result['serial'] = self._serial_file.timestamp()

			# HACK: together with the hack in 'WatchedFile' regarding
			#		mtime changes without content changes, the above 'serial'
			#		value might not change even if we need a refresh...
			#		so we include a dummy field that returns the
			#		current time
			result['timestamp'] = int(time())

			# Any real installer action can set the following variable
			# to indicate that the computer should be rebooted before
			# proceeding.
			result['reboot_required'] = self.ucr.is_true('update/reboot/required',False)

		except Exception, ex:
			typ = str(type(ex)).strip('<>')
			msg = '[while %s] [%s] %s' % (what,typ,str(ex))
			result['message'] = msg
			result['status'] = 1
			MODULE.error(msg)

		response.append(result)
		# ----------- DEBUG -----------------
		MODULE.info("updater/status returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(response).split("\n")
		for s in st:
				MODULE.info("   >> %s" % s)
		# -----------------------------------

		self.finished(request.id,response)

	def reboot(self,request):
		""" Reboots the computer. Simply invokes /sbin/reboot in the background
			and returns success to the caller. The caller is prepared for
			connection loss.
		"""
		result = True
		Popen(['/sbin/reboot']) # that's all
		self.finished(request.id,result)

	def running(self,request):
		""" Returns the id (key into INSTALLERS) of a currently
			running job, or the empty string if nothing is running.
		"""
		# ----------- DEBUG -----------------
		MODULE.info("updater/installer/running invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
				MODULE.info("   << %s" % s)
		# -----------------------------------

		result = self.__which_job_is_running()

		# ----------- DEBUG -----------------
		MODULE.info("updater/installer/running returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
				MODULE.info("   >> %s" % s)
		# -----------------------------------

		self.finished(request.id, result)

	def updater_log_file(self,request):
		""" returns the content of the log file associated with
			the job.

			Argument 'count' has the same meaning as already known:
			<0 ...... return timestamp of file (for polling)
			0 ....... return whole file as a string list
			>0 ...... ignore this many lines, return the rest of the file

			*** NOTE *** As soon as we have looked for a running job at least once,
						we know the job key and can associate it here.

			TODO: honor a given 'job' argument
		"""
		# ----------- DEBUG -----------------
		MODULE.info("updater/installer/logfile invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
				MODULE.info("   << %s" % s)
		# -----------------------------------
		result = None
		job = ''
		if self._current_job and 'job' in self._current_job:
			job = self._current_job['job']
		else:
			job = request.options.get('job','')

		count = request.options.get('count',0)
		if count < 0:
			result = 0
		else:
			result = []
		if not job in INSTALLERS:
			# job empty: this is the first call I can't avoid
			if job != '':
				MODULE.warn("   ?? Don't know a '%s' job" % job)
		else:
			if not 'logfile' in INSTALLERS[job]:
				MODULE.warn("   ?? Job '%s' has no associated log file" % job)
			else:
				fname = INSTALLERS[job]['logfile']
				if count < 0:
					result = self._logstamp(fname)
				else:
					# don't read complete file if we have an 'ignore' count
					if ('lines' in self._current_job) and (self._current_job['lines']):
						count += int(self._current_job['lines'])
					result = self._logview(fname, -count)

		# again debug, shortened
		if isinstance(result,int):
			MODULE.info("   >> %d" % result)
		else:
			MODULE.info("   >> %d lines" % len(result))

		# ----------- DEBUG -----------------
		MODULE.info("updater/installer/logfile returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
				MODULE.info("   >> %s" % s)
		# -----------------------------------

		self.finished(request.id, result)


	def updater_job_status(self,request):
		"""	Returns the content of the corresponding status file
			for a given job. Note that this is made a seperate function
			so we can call it even if the job is not running anymore. We need
			this to get the result of a job, and possibly the affordance to
			reboot.
		"""
		# ----------- DEBUG -----------------
		MODULE.info("updater/installer/status invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
				MODULE.info("   << %s" % s)
		# -----------------------------------

		# First check if a job is running. This will update the
		# internal field self._current_job, or if the job is finished,
		# it would return an empty string.
		inst = self.__which_job_is_running()

		job = request.options.get('job','')
		result = {}
		if job in INSTALLERS:
			# make a copy, not a reference!
#			result = {}
#			for arg in INSTALLERS[job]:
#				result[arg] = INSTALLERS[job][arg]
			result = deepcopy(INSTALLERS[job])

			if 'statusfile' in INSTALLERS[job]:
				try:
					for line in open(INSTALLERS[job]['statusfile']):
						fields = line.strip().split('=')
						if len(fields) == 2:
							result['_%s_' % fields[0]] = fields[1]
				except:
					pass
			# if we encounter that the frontend asks about the last job we
			# have executed -> include its properties too.
			if self._current_job:
				if self._current_job['job'] == job:
					for f in self._current_job:
						result[f] = self._current_job[f]
						if isinstance(result[f],str) and result[f].isdigit():
							result[f] = int(result[f])
				if inst == '':
					result['running'] = False
			else:
				# no job running but status for release was asked?
				# maybe the server restarted after job finished
				# and the frontend did not get that information
				# Bug #26318
				if job == 'release':
					result['detail'] = '%s-%s' % (self.ucr.get('version/version'), self.ucr.get('version/patchlevel'))
				else:
					result['detail'] = _('Unknown')

			# -------------- additional fields -----------------

			# elapsed time, ready to be displayed. (not seconds, but rather
			# the formatted string)
			if 'time' in result and 'started' in result:
				elapsed = result['time'] - result['started']
				if elapsed < 60:
					result['elapsed'] = '%ds' % elapsed
				else:
					mins = int(elapsed/60)
					secs = elapsed - (60 * mins)
					if mins < 60:
						result['elapsed'] = '%d:%02dm' % (mins,secs)
					else:
						hrs = int(mins/60)
						mins = mins - (60*hrs)
						result['elapsed'] = '%d:%02d:%02dh' % (hrs,mins,secs)
			# Purpose is now formatted in the language of the client (now that
			# this LANG is properly propagated to us)
			if 'purpose' in result:
				if result['purpose'].find('%') != -1:
					# make sure to not explode (Bug #26318), better show nothing
					if 'detail' in result:
						result['label'] = result['purpose'] % result['detail']
				else:
					result['label'] = result['purpose']
			# Affordance to reboot... hopefully this gets set before
			# we stop polling on this job status
			self.ucr.load()	# make it as current as possible
			result['reboot'] = self.ucr.is_true('update/reboot/required',False)

		# ----------- DEBUG -----------------
		MODULE.info("updater/installer/status returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
				MODULE.info("   >> %s" % s)
		# -----------------------------------

		self.finished(request.id,result)

	def run_installer(self,request):
		"""	This is the function that invokes any kind of installer. Arguments accepted:
			job ..... the main thing to do. can be one of:
				'release' ...... perform a release update
				'component' .... install a component by installing its default package(s)
				'distupgrade' .. update all currently installed packages (distupgrade)
				'check' ........ check what would be done for 'update' ... do we need this?
			detail ....... an argument that specifies the subject of the installer:
				for 'release' .... the target release number,
				for 'component' .. the component name,
				for all other subjects: detail has no meaning.

			Setup for this function is contained in the INSTALLERS structure
			at the top of the file.
		"""
		# ----------- DEBUG -----------------
		MODULE.info("updater/installer/execute invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
				MODULE.info("   << %s" % s)
		# -----------------------------------

		# Clean up any stored job details ... they're now obsolete.
		self._current_job = {}

		result = {}
		result['status'] = 0	# successful. If not: set result['message'] too.

		subject = request.options.get('job','')
		detail = request.options.get('detail','')
		if not subject in INSTALLERS:
			result['message'] = "Unknown installer job type '%s'" % subject
			result['status'] = RUN_PARAMETER_ERROR
			MODULE.warn(result['message'])
			self.finished(request.id,result)
			return

		MODULE.info("   ++ starting function '%s'" % subject)
		if not 'command' in INSTALLERS[subject]:
			result['message'] = "Function '%s' has no command" % subject
			result['status'] = RUN_PARAMETER_ERROR
			MODULE.warn(result['message'])
			self.finished(request.id,result)
			return

		# initial values of current job
		self._current_job = {
			'job':		subject,
			'detail':	detail,
			'logfile':	'',
			'lines':	0
		}

		# We want to limit the amount of logfile data being transferred
		# to the frontend. So we remember the line count of the associated
		# log file.
		if 'logfile' in INSTALLERS[subject]:
			fname = INSTALLERS[subject]['logfile']
			count = 0
			try:
				file = open(fname,'r')
				count = 0
				for line in file:
					count += 1
			finally:
				if file is not None:
					file.close()
			self._current_job['lines'] = count
			self._current_job['logfile'] = fname

		try:
			# Assemble the command line, now somewhat complicated:
			#
			#	(1)	take the 'command' entry from the INSTALLERS entry of this subject
			#	(2)	if it doesn't contain a percent sign -> ready.
			#	(3)	if it contains a percent sign: we must format something:
			#	(4)	if the subject is about 'component' we must get the 'defaultpackages'
			#		entry from the UCR tuple named by 'detail' and use that.
			#	(5)	if not, we can format the 'detail' field into the command.
			#
			# cmd = '%s' % INSTALLERS[subject]['command']		# I need a copy of this string!
			#
			cmd = INSTALLERS[subject]['command']
			if cmd.find('%') != -1:
				if subject == 'component':
					pkgs = ' '.join(self.uu.get_component_defaultpackage(detail))
					cmd = cmd % pkgs
					MODULE.info("  Resolution of default packages of the '%s' component:" % detail)
					MODULE.info("     PKGS = '%s'" % pkgs)
					MODULE.info("     CMD  = '%s'" % cmd)
				else:
					cmd = cmd % request.options.get('detail','')
			MODULE.info("   ++ Creating job: '%s'" % cmd)
			self.__create_at_job(cmd,detail)
		except Exception,ex:
			MODULE.warn("   ERROR: %s" % str(ex))

		# ----------- DEBUG -----------------
		MODULE.info("updater/installer/execute returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
				MODULE.info("   >> %s" % s)
		# -----------------------------------

		self.finished(request.id,result)


# ------------------------------------------------------------------------------
#
#		copied (and modified) from join module
#
# ------------------------------------------------------------------------------

	def _logstamp(self,fname):
		""" Logfile timestamp. Now a seperate function.
		"""
		try:
			st = stat(fname)
			if st:
				MODULE.info("   >> log file stamp = '%s'" % st[9])
				return st[9]
			return 0
		except:
			return 0

	def _logview(self,fname,count):
		""" Contains all functions needed to view or 'tail' an arbitrary text file.
			Argument 'count' can have different values:
			< 0 ... ignore this many lines, return the rest of the file
			0 ..... return the whole file, splitted into lines.
			> 0 ... return the last 'count' lines of the file. (a.k.a. tail -n <count>)
		"""
		lines = []
		try:
			file = open(fname,'r')
			for line in file:
				if (count < 0):
					count += 1
				else:
					l = line.rstrip()
					lines.append(l)
					if (count > 0) and (len(lines) > count):
						lines.pop(0)
		finally:
			if file is not None:
				file.close()
		return lines


# ------------------------------------------------------------------------------
#
#		copied from old Python module
#
# ------------------------------------------------------------------------------

	def __create_at_job(self, command, detail=''):
		""" Creates an 'at' job that will run the given command.
			Stores now the start time and the 'detail' request field into
			the job itself, so subsequent calls to '_which_job_is_running'
			can fully decode the purpose of the job (even localized!)
			and how long it is running.
		"""
		started = int(time())
		logfile = self._current_job['logfile']
		lines = self._current_job['lines']
		script = '''
#:started: %s
#:detail: %s
#:logfile: %s
#:lines: %s
#:command: %s
/usr/share/univention-updater/disable-apache2-umc
%s < /dev/null
/usr/share/univention-updater/enable-apache2-umc --no-restart
''' % (started,detail,logfile,lines,command,command)
		p1 = subprocess.Popen( [ 'LC_ALL=C at now', ], stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True )
		(stdout,stderr) = p1.communicate( script )

		if p1.returncode != 0:
			return (p1.returncode,stderr)
		else:
			return (p1.returncode,stdout)

	def __which_job_is_running(self):
		"""	Checks all currently running AT jobs if there's one of our
			predefined INSTALLER jobs.

			Additionally, this function parses the properties of the job and
			stores them in the member variable _current_job {}. This will keep
			the last seen state even if the job is already finished.
		"""
		p1 = subprocess.Popen('/usr/bin/atq',stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		(atqout,stderr) = p1.communicate()
		for line in atqout.splitlines():
			job = line.split('\t',1)[0]
			if job.isdigit():
				p2 = subprocess.Popen(['/usr/bin/at','-c',job], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
				(atout,stderr) = p2.communicate()
				for inst in INSTALLERS:
					if 'command' in INSTALLERS[inst]:
						cmd = INSTALLERS[inst]['command'].split('%')[0]
						MODULE.info("   ++ Checking for '%s'" % cmd)
						if cmd in atout:
# cleaning up is done in 'run_installer()'
#							self._current_job = {}
							self._current_job['job'] = inst				# job key
							self._current_job['running'] = True			# currently running: we have found it per 'at' job
							self._current_job['time'] = int(time())		# record the last time we've seen this job
							for line in atout.split("\n"):
								match = re.search('^\#\:([a-z]+)\:\s(.*)$',line)
								if (match):
									var = match.group(1)
									val = match.group(2)
									# restore numeric strings into numbers!
									if val.isdigit():
										self._current_job[var] = int(val)
									else:
										self._current_job[var] = val
							return inst
		return ''

