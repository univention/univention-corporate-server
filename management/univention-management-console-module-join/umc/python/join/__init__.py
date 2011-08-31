#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: system usage statistics
#
# Copyright 2011 Univention GmbH
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

import pprint
import subprocess
import univention.management.console as umc
import univention.management.console.modules as umcm

import re
from os import stat,listdir,chmod,unlink,path
from locale import nl_langinfo,D_T_FMT
from time import strftime,localtime,sleep
from string import join
from subprocess import Popen

from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import *

_ = umc.Translation('univention-management-console-module-join').translate

class Instance(umcm.Base):
	def init(self):
		MODULE.warn("Initializing 'join' module with LANG = '%s'" % self.locale)
		global _
		_ = umc.Translation('univention-management-console-module-join',self.locale).translate

		# some constants
		self._instdir		= '/usr/lib/univention-install'				# where to find *.inst files
		self._statusfile	= '/var/univention-join/status'				# where to find last run versions
		self._logname		= '/var/log/univention/join.log'			# join log file name
		self._jointool		= '/usr/sbin/univention-join'				# the tool to call for a full join
		self._tempscript	= '/tmp/umc_join_runscripts.sh'				# temp script name for invoking scripts
		self._tempfile		= '/tmp/umc_join.tmp'						# file to use if the script itself needs a temp file
		self._passfile		= '/tmp/ucs_join_pass.tmp'					# password for join tool must be given in a file


		# Will hold the object of the subprocess as long as scripts are running.
		# Can be queried with the 'join/running' query.
		self._process		= None

	def query(self,request):
		"""Dispatcher for different query scopes."""
		# ----------- DEBUG -----------------
		MODULE.info("join/query invoked with:")
		MODULE.info("   << LANG = '%s'" % self.locale)
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
			MODULE.info("   << %s" % s)
		# -----------------------------------
		result = []
		# please don't bite me, rather tell me how to write a 'case' in Python
		scope = request.options.get('scope','')
		# list join scripts and their status
		if scope == 'scripts':
			result = self._scripts()
			request.status = SUCCESS
		# list join log (or log file stamp, for tail-like display)
		elif scope == 'logview':
			# let it fail if arg is not numerical
			result = self._logview(int(request.options.get('count',10)))
			request.status = SUCCESS
		# ask for the join date (file timestamp of the 'joined' status file)
		elif scope == 'joined':
			result = self._joined()
			request.status = SUCCESS
		# check if a subprocess is running
		elif scope == 'running':
			result = self._running()
			request.status = SUCCESS
		else:
			request.status = FAILURE

		# PURE DEBUG: print all that we'll return
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
			MODULE.info("   >> %s" % s)

		self.finished(request.id,result)

	def join(self,request):
		"""runs the 'univention-join' script for a unjoined system with
		the given arguments."""
		result = ''
		args = []		# argument list to univention-join
		host = request.options.get('host','')
		if host != '':
			args.append('-dcname')
			args.append(host)
		user = request.options.get('user','')
		if user != '':
			args.append('-dcaccount')
			args.append(user)
		# Password is not given on command line, instead we have
		# to write a file for that.
		pasw = request.options.get('pass','')
		if pasw != '':
			args.append('-dcpwd')
			args.append(self._passfile)
			file = None
			try:
				file = open(self._passfile,'w')
				file.write("%s\n" % pasw)
			finally:
				if file != None:
					file.close()
					chmod(self._passfile,0400)
		# construct a batch file that will do everything
		cmds = [
			'#!/bin/bash',
			'TMPF=%s' % self._tempfile,
			'trap "rm -f %s %s %s" EXIT' % (self._passfile, self._tempfile, self._tempscript),
			'(',
			'  echo "`date`: Starting univention-join"',
			'  %s %s >${TMPF} 2>&1' % (self._jointool,join(args)),
			'  ret=$?',
			'  if [ ${ret} = 0 ] ; then',
			'    echo "`date`: univention-join finished successfully"',
			'  else',
			'    echo "`date`: univention-join finished with error:"',
			'    /usr/bin/tail -n 7 ${TMPF}',
			'  fi',
			'  echo',
			') >>%s 2>&1' % self._logname
		]
		result = self._run_shell_script(cmds)
		request.status = SUCCESS
		self.finished(request.id,result)

	def run(self,request):
		"""runs the given join scripts (args is an array) Note that we
		don't rely on sortedness or even existance of the script names
		passed in. Everything is checked here before we fire the real
		action."""
		result = ''
		scripts = request.options.get('scripts',[])
		current = self._script_map()

		# Temporary shell script that will call the scripts,
		# redirect their output (STDERR + STDOUT) into the
		# log file, and logs their exit code.
		cmds = [
			'#!/bin/bash',
			'trap "rm -f $0" EXIT',
			'function run()',
			'{',
			'  echo "`date`: running $1"',
			'  ./$1',
			'  local ret=$?',
			'  echo "`date`: $1 finished with ${ret}"',
			'  echo',
			'}',
			'('
			'  cd %s' % self._instdir
		]
		if len(scripts):
			fnames = []		# array for the full filenames of scripts, must be sorted by priority numbers
			MODULE.info("Running selected join scripts:")
			for s in scripts:
				if not s in current:
					MODULE.warn("   !! Script name '%s' is illegal" % s)
				else:
					fnames.append(current[s]['full'])
			for s in sorted(fnames):
				MODULE.info('   .. %s' % s)
				cmds.append('  run %s' % s)
			cmds.append(') >>%s 2>&1' % self._logname)

			result = self._run_shell_script(cmds)
			request.status = SUCCESS

		self.finished(request.id,result)

	def _run_shell_script(self,cmds):
		"""internal helper for running a script:
		 -	arg is a list of lines to write into a temporary shell script
		 -	create that script, flag it executable
		 -	create process, store in self._process
		 -	on any error, returns error text, else empty string"""
		if path.exists(self._tempscript):
			# this is shown at the frontend, so we have to translate it.
			return _("Another join operation is in progress")
		file = None
		try:
			MODULE.info("Creating temporary script:")
			file = open(self._tempscript,'w')
			for line in cmds:
				MODULE.info("   ++ %s" % line)
				file.write("%s\n" % line)
			file.close()
			chmod(self._tempscript,0700)
			self._process = Popen(self._tempscript)
		except Exception, ex:
			self._process = None
			if file != None:
				file.close()
			if path.exists(self._tempscript):
				unlink(self._tempscript)
			MODULE.warn("ERROR: %s" % str(ex))		# print to module log
			return str(ex)
		return ''

	def _joined(self):
		"""returns (localized) the join date+time (or empty string if not joined)"""
		try:
			st = stat('/var/univention-join/joined')
			if st:
				# FIXME Locale info of the process is not right!
				fmt = nl_langinfo(D_T_FMT)		# string to format a date/time
				tim = localtime(st[9])
				txt = strftime(fmt,tim)
				return txt
		except:
			return ''

	def _script_map(self):
		"""Helper function that returns a dict of currently available join scripts.
		Key is the 'basename', value is a dict with relevant keys:-
			'script' ... basename of the script
			'full' ..... real file name
			'prio' ..... priority number, must be honored if we're running multiple scripts
			'current' .. the version number as read from the script itself"""
		# List all join scripts (*.inst) in /usr/lib/univention-install
		MODULE.info("Listing scripts in '%s'" % self._instdir)
		files = {}		# key = basename, value = dict with properties
		for fname in listdir(self._instdir):
			match = re.search('^(\d+)(.*)\.inst$',fname)
			if match:
				entry = {}
				entry['full'] = fname				# full file name
				entry['script'] = match.group(2)	# basename without prio and '.inst'
				entry['prio'] = match.group(1)		# script priority

				file = None
				try:
					file = open('%s/%s' % (self._instdir,fname))
					for line in file:
						match = re.search('^VERSION\=(\d+)',line)
						if match:
							entry['current'] = match.group(1)
							MODULE.info("   Script '%s' has version '%s'" % (fname,match.group(1)))
							break	# should stop reading from this file
				finally:
					if file != None:
						file.close()
					# should never happen, but...
					if not 'current' in entry:
						MODULE.warn("   Script '%s' has no version number" % fname)
					else:
						files[entry['script']] = entry
		MODULE.info("Found %d valid scripts." % len(files))		
		return files

	def _scripts(self):
		"""collects status about join scripts, returns ready-formatted
		grid data.  if machine is not joined -> returns an empty array."""
		jtx = self._joined()
		if not len(jtx):
			MODULE.warn("   System not joined -> returning empty script list.")
			result = []
			return result
		# get list of join scripts
		files = self._script_map()

		# read status file /var/univention-join/status
		# <scriptname> v<version> <status>
		#
		# Assigns remaining properties to the corresponding entry of files{}

		MODULE.info("   .. Parsing '%s' ..." % self._statusfile)
		file = None
		lcount = 0			# line count
		fcount = 0			# file count
		try:
			file = open(self._statusfile)
			for line in file:
				lcount = lcount + 1
				temp = line.split()
				if len(temp) != 3:
					next
				if temp[2] != 'successful':
					next
				fcount = fcount + 1
				(fname,version,status) = temp
				version = version.replace('v','')
				if fname in files:
					# Some join scripts fail to remove older entries from the status
					# file, so we have to check that we've catched the highest version!
					if 'last' in files[fname]:					# we have already registered an instance of this script, and...
						if version < files[fname]['last']:		# ... it has a higher version than the one we're processing, so...
							next								# ... ignore this entry
					files[fname]['last'] = version
					if files[fname]['last'] < files[fname]['current']:
						files[fname]['icon'] = 'join-run'
						files[fname]['action'] = _('run')
						files[fname]['status'] = _('due')
					else:
						files[fname]['status'] = _('successful')
						files[fname]['icon'] = 'join-success'
						files[fname]['action'] = ''
				else:
					MODULE.warn("  Script '%s' has no package" % fname)
					e = {}
					e['script'] = fname
					e['status'] = _('not installed')
					e['icon'] = 'join-error'
					e['last'] = version
					files[fname] = e
		except Exception,ex:
			MODULE.warn("ERROR: %s" % str(ex))
		finally:
			if file != None:
				file.close()
		MODULE.info("   .. Read %d lines, extracted %d success entries" % (lcount,fcount))
		# Say it perlish: @result = values %files;
		result = []
		for idx in files:
			entry = files[idx]
			if not 'last' in entry:
				entry['last'] = '--'
				if 'current' in entry:
					entry['status'] = _('never run')
					entry['icon'] = 'join-run'
					entry['action'] = _('run')
			# to avoid double expressions in the JS code, checking for
			# definedness and non-emptiness of strings: We set all empty
			# properties to the empty string.
			if not 'action' in entry:
				entry['action'] = ''
			if not 'icon' in entry:
				entry['icon'] = ''
			# Return only entries that have a 'current' property.
			if 'current' in entry:
				result.append(entry)
		return result

	def _logview(self,count):
		"""Contains all functions needed to view or 'tail' the join log.
		Argument 'count' can have different values:
		< 0 ... return Unix timestamp of log file, to avoid fetching unchanged file.
		0 ..... return the whole file, splitted into lines.
		> 0 ... return the last 'count' lines of the file. (a.k.a. tail)"""
		lines = []
		if count < 0:
			try:
				st = stat(self._logname)
				if st:
					MODULE.info("   >> log file stamp = '%s'" % st[9])
					return st[9]
				return 0
			except:
				return 0
		try:
			file = open(self._logname,'r')
			for line in file:
				l = line.rstrip()
				lines.append(l)
				if (count) and (len(lines) > count):
					lines.pop(0)
		finally:
			if file != None:
				file.close()
		return lines

	def _running(self):
		"""Polling function that checks if our subprocess is running or
		finished in the meantime."""
		# do we have a process running?
		if self._process != None:
			# already terminated?
			if self._process.poll() != None:
				# unregister it.
				self._process = None
				# Clean up temp files
				for f in [self._tempscript, self._tempfile, self._passfile ]:
					if path.exists(f):
						MODULE.warn(_("Removing temp file: %s" % f))
						unlink(f)
			# true if running, false if not.
			return (self._process != None)
		# If we're a different module instance than the one that holds the
		# currently running process -> check for existance of the script
		# file and return true if we see one.
		else:
			return (path.exists(self._tempscript))

