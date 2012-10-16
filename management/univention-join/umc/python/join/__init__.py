#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: system usage statistics
#
# Copyright 2011-2012 Univention GmbH
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
import subprocess
import os
import stat
import tempfile
import base64
import ldap
import pipes
import pprint
import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.management.console.config import ucr

import re
from os import listdir,chmod,unlink,path, umask
from locale import nl_langinfo,D_T_FMT
from time import strftime,localtime
from string import join
from subprocess import Popen
import notifier.threads
import univention.uldap
import univention.admin.uldap
import univention.admin.modules

from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import *

_ = umc.Translation('univention-management-console-module-join').translate

class JoinExceptionUnknownHost(Exception):
	pass
class JoinExceptionInvalidCredentials(Exception):
	pass
class JoinExceptionInvalidCharacters(Exception):
	pass
class JoinExceptionUnknownError(Exception):
	pass

class Instance(umcm.Base):
	def __init__( self ):
		umcm.Base.__init__( self )
		# reset umask to default
		umask( 0022 )

	def init(self):
		MODULE.warn("Initializing 'join' module with LANG = '%s'" % self.locale)

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
		""" Query to fill the scripts grid. """
		# ----------- DEBUG -----------------
		MODULE.info("join/query invoked with:")
		MODULE.info("   << LANG = '%s'" % self.locale)
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
			MODULE.info("   << %s" % s)
		# -----------------------------------
		result = self._scripts()
		request.status = SUCCESS

		# ---------- DEBUG --------------
		MODULE.info("join/query returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
			MODULE.info("   >> %s" % s)
		# --------------------------------

		self.finished(request.id,result)

	def joined(self,request):
		""" returns the (localized) join date/time or
			the empty string.
		"""
		# ----------- DEBUG -----------------
		MODULE.info("join/joined invoked with:")
		MODULE.info("   << LANG = '%s'" % self.locale)
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
			MODULE.info("   << %s" % s)
		# -----------------------------------

		result = self._joined()
		request.status = SUCCESS

		# ---------- DEBUG --------------
		MODULE.info("join/joined returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
			MODULE.info("   >> %s" % s)
		# --------------------------------

		self.finished(request.id,result)

	def running(self,request):
		""" returns true if a join script is running.
		"""
		# ----------- DEBUG -----------------
		MODULE.info("join/running invoked with:")
		MODULE.info("   << LANG = '%s'" % self.locale)
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
			MODULE.info("   << %s" % s)
		# -----------------------------------

		result = self._running()
		request.status = SUCCESS

		# ---------- DEBUG --------------
		MODULE.info("join/running returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
			MODULE.info("   >> %s" % s)
		# --------------------------------

		self.finished(request.id,result)

	def logview(self,request):
		""" Frontend to the _logview() function: returns
			either the timestamp of the log file or
			some log lines.
		"""
		# ----------- DEBUG -----------------
		MODULE.info("join/logview invoked with:")
		MODULE.info("   << LANG = '%s'" % self.locale)
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
			MODULE.info("   << %s" % s)
		# -----------------------------------

		result = self._logview(int(request.options.get('count',10)))
		request.status = SUCCESS

		# ---------- DEBUG --------------
		# TODO: We should not repeat the whole log into
		# the module log file!
		MODULE.info("join/logview returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
			MODULE.info("   >> %s" % s)
		# --------------------------------

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

	def _ldapsearch_wrapper_decode64_dnfilter(self, lines):
		reBase64 = re.compile('^([a-zA-Z0-9-]*):: (.*)')

		# decode base64 encoded ldapsearch result lines
		def decode64(txt):
			if reBase64.match(txt):
				attr, data = txt.split(':: ',1)
				return '%s: %s' % (attr, base64.decodestring(data))
			return txt

		# unwrap lines from ldapsearch
		result = []
		linecache = ''
		for line in lines.splitlines():
			if line[:1] == ' ' and line[:2] != '  ':
				linecache += line[1:]
			else:
				if linecache:
					result.append(decode64(linecache))
				linecache = line
		result.append(decode64(linecache))

		# filter out lines with object DN
		for line in result:
			if line.startswith('DN: ') or line.startswith('dn: '):
				return line[4:]

		return ''


	# regular expression to match warnings
	_regWarnings = re.compile(r'^Warning:.*?\n', re.MULTILINE)

	def _guess_userdn(self, username, password, hostname):
		# do some security checks on given username and hostname
		# Warning: no complete check since the user is able to log on to the DC master and can call harmful commands directly
		invalid_characters = """'"$();"""
		for i in invalid_characters:
			if i in username:
				raise JoinExceptionInvalidCharacters(_('The username contains an invalid character: %s') % i)
			if i in hostname:
				raise JoinExceptionInvalidCharacters(_('The hostname contains an invalid character: %s') % i)

		# create temporary password file
		pwdfilename = tempfile.mkstemp()[1]
		os.chown(pwdfilename, 0, 0)
		os.chmod(pwdfilename, stat.S_IRUSR | stat.S_IWUSR)
		open(pwdfilename,'w').write('%s\n' % password)

		user_host = '%s@%s' % (username, hostname)

		# TODO: the following shell calls are also present in "univention-join";
		#       move them to a new script "univention-guess-userdn" and
		#		call this new script from univention-join and from here via
		#       univention-ssh while joining.
		#
		# Original commands from script "univention-join"
		# univention-ssh "$DCPWD" "$DCACCOUNT"@"$DCNAME" /usr/sbin/udm users/user list --filter uid=$DCACCOUNT --logfile /dev/null | sed -ne 's|DN: ||p'
		# univention-ssh "$DCPWD" "$DCACCOUNT"@"$DCNAME" ldapsearch -x -LLL -H ldapi:/// "\'(&(uid=$DCACCOUNT)(objectClass=person))\'" dn | ldapsearch-wrapper | ldapsearch-decode64 | sed -ne 's|^dn: ||p;s|^DN: ||p'
		# univention-ssh "$DCPWD" "$DCACCOUNT"@"$DCNAME" ldapsearch -x -LLL "\'(&(uid=$DCACCOUNT)(objectClass=person))\'" dn | ldapsearch-wrapper | ldapsearch-decode64 | sed -ne 's|^dn: ||p;s|^DN: ||p'
		cmdlist = [	['univention-ssh', pwdfilename, user_host, '/usr/sbin/udm', 'users/user', 'list', '--filter', 'uid=%s' % username, '--logfile', '/dev/null'],
					['univention-ssh', pwdfilename, user_host, 'ldapsearch', '-x', '-LLL', '-H', 'ldapi:///', '''"\'(&(uid=%s)(objectClass=person))\'"''' % username, 'dn' ],
					['univention-ssh', pwdfilename, user_host, 'ldapsearch', '-x', '-LLL', '''"\'(&(uid=%s)(objectClass=person))\'"''' % username, 'dn' ],
					]

		try:
			for cmd in cmdlist:
				# call univention-ssh and try to determine userDn
				stdout, stderr = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
				if stderr:
					MODULE.error('calling %s failed:\n%s' % (cmd, stderr))
				if 'could not resolve hostname' in stderr.lower() or 'name or service not known' in stderr.lower():
					raise JoinExceptionUnknownHost()
				if 'permission denied' in stderr.lower():
					raise JoinExceptionInvalidCredentials()
				stderr = self._regWarnings.sub('', stderr)  # ignore warnings
				if stderr:
					raise JoinExceptionUnknownError()

				userdn = self._ldapsearch_wrapper_decode64_dnfilter(stdout)
				if userdn:
					return userdn

			return None
		finally:
			os.remove(pwdfilename)


	def join(self,request):
		"""runs the 'univention-join' script for a unjoined system with
		the given arguments."""


		def _thread( request ):
			result = {}
			host = request.options.get('host')
			user = request.options.get('user')
			password = request.options.get('pass')

			try:
				if not self._guess_userdn(user, password, host):
					result['msg'] = _("The given user does not exist in LDAP. Please enter a domain administrator account.")
					result['title'] = _('Wrong credentials')
			except JoinExceptionUnknownHost:
				result['msg'] = _("The given hostname cannot be resolved or the host is unreachable.")
				result['title'] = _('Host unreachable')
			except JoinExceptionInvalidCredentials:
				result['msg'] = _("The given username or password is not correct.")
				result['title'] = _('Wrong credentials')
			except JoinExceptionUnknownError:
				result['msg'] = _("An unknown error occured while testing join credentials.")
				result['title'] = _('Error')
			except JoinExceptionInvalidCharacters, e:
				result['msg'] = str(e)
				result['title'] = _('Invalid characters')

			if result:
				result['errortype'] = 'autherror'
				request.status = SUCCESS
				self.finished(request.id, result)
				return

			# create temporary password file
			self._passfile = tempfile.mkstemp()[1]
			os.chown(self._passfile, 0, 0)
			os.chmod(self._passfile, stat.S_IRUSR | stat.S_IWUSR)
			open(self._passfile, 'w').write('%s\n' % password)

			args = ['-dcname', host, '-dcaccount', user, '-dcpwd', self._passfile]		# argument list to univention-join

			# construct a batch file that will do everything
			cmds = [
				'#!/bin/bash',
				'TMPF=%s' % self._tempfile,
				'trap "rm -f %s %s %s" EXIT' % (self._passfile, self._tempfile, self._tempscript),
				'(',
				'  echo "`date`: Starting univention-join"',
				'  /usr/share/univention-updater/disable-apache2-umc',  # disable UMC server components restart
				'  %s %s >${TMPF} 2>&1' % (self._jointool,join(args)),
				'  ret=$?',
				'  if [ ${ret} = 0 ] ; then',
				'	 echo "`date`: univention-join finished successfully"',
				'  else',
				'	 echo "`date`: univention-join finished with error:"',
				'	 /usr/bin/tail -n 7 ${TMPF}',
				'  fi',
				'  echo',
				'  /usr/share/univention-updater/enable-apache2-umc --no-restart',  # enable UMC server components restart
				') >>%s 2>&1' % self._logname
			]
			msg = self._run_shell_script(cmds)
			if msg:
				result['msg'] = msg
				result['errortype'] = 'joinerror'
			request.status = SUCCESS
			self.finished(request.id, result)

		localthread = notifier.threads.Simple( 'join', notifier.Callback( _thread, request ),
										  notifier.Callback( self._thread_finished, request ) )
		localthread.run()


	def run(self,request):
		"""runs the given join scripts (args is an array) Note that we
		don't rely on sortedness or even existance of the script names
		passed in. Everything is checked here before we fire the real
		action."""
		result = {}
		credentials = []
		username = request.options.get('username',[])
		password = request.options.get('password',[])
		scripts = request.options.get('scripts',[])
		current = self._script_map()

		ucr.load()
		baseDn = ucr.get('ldap/base')

		# If username and password are set then check credentials against master
		# before calling join script.
		MODULE.info('username = %s' % username)
		if username and password:
			userDn = None
			try:
				# get LDAP connection and UDM users/user module
				lo = univention.uldap.getMachineConnection()
				position = univention.admin.uldap.position(baseDn)
				univention.admin.modules.update()
				user_module = univention.admin.modules.get("users/user")
				univention.admin.modules.init(lo, position, user_module)

				# find desired object
				objects = univention.admin.modules.lookup(user_module, None, lo, scope='sub', filter='uid=%s' % username)

				if not objects:
					MODULE.warn('The given username "%s" does not exist.' % username)
					result['msg'] = _('The given username "%s" does not exist.') % username
				elif len(objects) > 1:
					MODULE.error('Found more than one matching user object for uid=%s.'% username)
					result['msg'] = _('Found more than one matching user object.')
				else:
					userDn = objects[0].dn
					MODULE.info('userDn = %s' % userDn)
					credentials = [ '--binddn', userDn, '--bindpwd', password ]

					port = int(ucr.get('ldap/master/port', '7389'))
					lo = univention.uldap.access(host=ucr['ldap/master'], port=port,
												 base=ucr['ldap/base'],
												 binddn=userDn, bindpw=password,
												 start_tls=2, decode_ignorelist=[])
			except ldap.INVALID_CREDENTIALS, e:
				MODULE.warn('The given credentials are not correct.')
				result['msg'] = _('The given credentials are not correct.')
			except ldap.SERVER_DOWN, e:
				MODULE.error('Cannot connect to LDAP server for resolving username.')
				result['msg'] = _('Cannot connect to LDAP server for resolving username.')

			if result.get('msg'):
				# error status
				result['errortype'] = 'autherror'
				request.status = SUCCESS
				self.finished(request.id, result)
				return

		# Temporary shell script that will call the scripts,
		# redirect their output (STDERR + STDOUT) into the
		# log file, and logs their exit code.
		cmds = [
			'#!/bin/bash',
			'trap "rm -f $0" EXIT',
			'function run()',
			'{',
			'  echo "`date`: running $1"',
			'  /usr/share/univention-updater/disable-apache2-umc',  # disable UMC server components restart
			'  local cmd="$1"; shift',
			'  ./$cmd "$@"',
			'  local ret=$?',
			'  echo "`date`: $cmd finished with exitcode ${ret}"',
			'  echo',
			'  /usr/share/univention-updater/enable-apache2-umc --no-restart',  # enable UMC server components restart
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
				if credentials:
					cmd = '%s %s' % (s, ' '.join([ pipes.quote(x) for x in credentials]))
					MODULE.info('   .. %s' % cmd)
					cmds.append('  run %s' % cmd)
				else:
					MODULE.info('   .. %s' % s)
					cmds.append('  run %s' % s)
			cmds.append(') >>%s 2>&1' % self._logname)

			result['msg'] = self._run_shell_script(cmds)
			if result['msg']:
				result['errortype'] = 'scripterror'
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
			st = os.stat('/var/univention-join/joined')
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
							try:
								entry['current'] = int(match.group(1))
								MODULE.info("   Script '%s' has version '%s'" % (fname,match.group(1)))
								break	# should stop reading from this file
							except ValueError, e:
								MODULE.warn("   Failed to parse version number for Script '%s': VERSION=%s" % (fname, match.group(1)))
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
			try:
				for line in file:
					lcount = lcount + 1
					temp = line.split()
					if len(temp) != 3:
						continue
					if temp[2] != 'successful':
						continue
					fcount = fcount + 1
					(fname,version,status) = temp
					try:
						version = int(version.replace('v',''))
					except ValueError, e:
						version = 0
						MODULE.warn("   Failed to parse executed version number for Script '%s': %s" % (fname, version))
					if fname in files:
						# Some join scripts fail to remove older entries from the status
						# file, so we have to check that we've catched the highest version!
						if version < files[fname].get('last', 0):
							# ignore smaller version
							continue
						files[fname]['last'] = version
						if files[fname].get('last', 0) < files[fname].get('current', 0):
							files[fname]['action'] = _('run')
							files[fname]['status'] = _('due')
						else:
							files[fname]['status'] = _('successful')
							files[fname]['action'] = ''
					else:
						MODULE.warn("  Script '%s' has no package" % fname)
						e = {}
						e['script'] = fname
						e['status'] = _('not installed')
						e['last'] = version
						files[fname] = e
			finally:
				file.close()
		except (IOError, OSError), e:
			MODULE.warn("ERROR opening the status file: %s" % e)
		MODULE.info("   .. Read %d lines, extracted %d success entries" % (lcount,fcount))
		# Say it perlish: @result = values %files;
		result = []
		for idx in files:
			entry = files[idx]
			if not 'last' in entry:
				entry['last'] = '--'
				if 'current' in entry:
					entry['status'] = _('never run')
					entry['action'] = _('run')
			# to avoid double expressions in the JS code, checking for
			# definedness and non-emptiness of strings: We set all empty
			# properties to the empty string.
			if not 'action' in entry:
				entry['action'] = ''
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
				st = os.stat(self._logname)
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
						MODULE.warn("Removing temp file: %s" % f)
						unlink(f)
			# true if running, false if not.
			return (self._process != None)
		# If we're a different module instance than the one that holds the
		# currently running process -> check for existance of the script
		# file and return true if we see one.
		else:
			return (path.exists(self._tempscript))

