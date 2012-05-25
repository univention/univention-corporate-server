#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Common Python Library
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

'''This module abstracts the handling of at-jobs, each job is encapsulated by
the class AtJob. Use the method add() in order to add a new command to the
queue of at-jobs. Use the methods list() and load() to get a list of all
registered jobs or to load a specific job given an ID, respectively. The module
uses time stamps in seconds for scheduling jobs.'''

import datetime
import subprocess
import re
import locale

__all__ = [ 'add', 'list', 'load', 'remove', 'reschedule', 'AtJob' ]

# internal formatting strings and regexps
_regWhiteSpace = re.compile(r'\s+')
_regJobNr = re.compile(r'job\s+(\d+)')
_dateTimeFormatRead = '%a %b %d %H:%M:%S %Y'
_dateTimeFormatWrite = '%Y-%m-%d %H:%M'
_timeFormatWrite = '%H:%M'
_dateFormatWrite = '%Y-%m-%d'

SCRIPT_PREFIX = '# --- Univention-Lib at job  ---'
COMMENT_PREFIX = '# Comment: '

def add( cmd, execTime = None, comments = {} ):
	'''Add a new command to the job queue given a time (in seconds since
	the epoch or as a datetime object) at which the job will be
	executed. Optionally comments can be provided as a dictionary. The
	data is assoziated with the job.'''

	if isinstance( execTime, ( int, float ) ):
		start = datetime.datetime.fromtimestamp( execTime )
	else:
		start = execTime

	# launch the at job directly
	atCmd = ['/usr/bin/at']
	if start:
		jobTime = start.strftime( _timeFormatWrite )
		jobDate = start.strftime( _dateFormatWrite )
		atCmd.extend([jobTime, jobDate])
	else:
		atCmd.append('now')

	# add comments
	if comments:
		cmd =  '\n'.join( map( lambda c: '%s%s:%s' % ( COMMENT_PREFIX, c[ 0 ], c[ 1 ] ), comments.items() ) ) + '\n' + SCRIPT_PREFIX + '\n' + cmd

	# add job
	p = subprocess.Popen(atCmd, stdout = subprocess.PIPE, stdin = subprocess.PIPE, stderr = subprocess.PIPE)

	# send the job to stdin
	out = p.communicate(cmd)

	# parse output and return job
	matches = _regJobNr.findall('\n'.join(out))
	if matches:
		return load(int(matches[0]))
	return None

def reschedule( nr, execTime = None ):
	"""Re-schedules the at job with the given number for the specified time"""
	atjob = load( nr, extended = True )
	if atjob is None:
		raise AttributeError( 'Could not find at job %s' % nr )
	if atjob.command is None:
		raise AttributeError( 'The command of the at job is not available' )
	atjob.rm()

	return add( atjob.command, execTime, atjob.comments )

def list( extended = False ):
	'''Returns a list of all registered jobs as instances of AtJob. If
	extended is set to True the parser also extras the comments and the
	command to execute. This can be used to re-schedule a job.'''
	p = subprocess.Popen('/usr/bin/atq', stdout = subprocess.PIPE, stderr = subprocess.PIPE)
	jobs = []
	for line in p.stdout:
		ijob = _parseJob(line)
		if ijob:
			jobs.append(_parseJob(line))

	if extended:
		for job in jobs:
			_parseScript( job )

	return jobs

def load( nr, extended = False ):
	'''Load a job given a particular ID. Returns None if job does not exist,
	otherwise an instance of AtJob is returned.'''
	result = [ p for p in list( extended ) if p.nr == nr ]
	if len(result):
		return result[0]
	return None

def remove( nr ):
	"""Removes the at job with the given number"""
	result = [ p for p in list() if p.nr == nr ]
	if len(result):
		return result[ 0 ].rm()

def _parseScript( job ):
	p = subprocess.Popen( [ '/usr/bin/at', '-c', str( job.nr ) ], stdout = subprocess.PIPE )
	job.comments = {}
	script = False
	job.command = ''
	for line in p.stdout:
		if script:
			job.command += line
			continue
		if line.startswith( COMMENT_PREFIX ):
			line = line[ len( COMMENT_PREFIX ) : -1 ]
			key, value = line.split( ':', 1 )
			job.comments[ key ] = value
		elif line.startswith( SCRIPT_PREFIX ):
			script = True

def _parseJob(string):
	'''Internal method to parse output of at-command.'''
	timeLocale = locale.getlocale(locale.LC_TIME)
	try:
		# change the time locale temporarily to 'C' as atq uses English date format
		# ignoring the currently set locale
		locale.setlocale(locale.LC_TIME, 'C')

		# parse string
		tmp = _regWhiteSpace.split(string)
		execTime = datetime.datetime.strptime( ' '.join( tmp[ 1 : 6 ] ), _dateTimeFormatRead )
		isRunning = tmp[6] == '='
		owner = tmp[7]
		nr = int(tmp[0])
	except (IndexError, ValueError), e:
		# parsing failed
		return None
	finally:
		# reset locale to default
		locale.setlocale(locale.LC_TIME, timeLocale)
	return AtJob(nr, owner, execTime, isRunning)


class AtJob(object):
	'''This class is an abstract representation of an at-job. Do not initiate
	the class directly, but use the methods provided in this module.'''

	def __init__(self, nr, owner, execTime, isRunning):
		self.nr = nr
		self.owner = owner
		self.command = None
		self.execTime = execTime
		self.isRunning = isRunning
		self.comments = {}

	def __str__(self):
		t = self.execTime.strftime( _dateTimeFormatWrite )
		if self.isRunning:
			t = 'running'
		return 'Job #%d (%s)' % (self.nr, t)

	def __repr__(self):
		return self.__str__()

	def rm(self):
		'''Remove the job from the queue.'''
		p = subprocess.Popen(['/usr/bin/atrm', str(self.nr)], stdout = subprocess.PIPE, stderr = subprocess.PIPE)

