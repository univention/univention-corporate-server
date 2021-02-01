#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright 2012-2021 Univention GmbH
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

"""
Univention common Python library for handling :program:`at` jobs.

This module abstracts the handling of at-jobs, each job is encapsulated by
the class :py:class:`AtJob`. Use the method :py:meth:`add` in order to add a new command to the
queue of at-jobs. Use the methods :py:meth:`list` and :py:meth:`load` to get a list of all
registered jobs or to load a specific job given an ID, respectively. The module
uses time stamps in seconds for scheduling jobs.
"""

import datetime
import subprocess
import re
import locale
from typing import Dict, List, Mapping, Optional, Union  # noqa F401

__all__ = ['add', 'list', 'load', 'remove', 'reschedule', 'AtJob']

# internal formatting strings and regexps
_regWhiteSpace = re.compile(r'\s+')
_regJobNr = re.compile(r'job\s+(\d+)'.encode('ASCII'))
_dateTimeFormatRead = '%a %b %d %H:%M:%S %Y'
_dateTimeFormatWrite = '%Y-%m-%d %H:%M'
_timeFormatWrite = '%H:%M'
_dateFormatWrite = '%Y-%m-%d'

SCRIPT_PREFIX = '# --- Univention-Lib at job  ---'
COMMENT_PREFIX = '# Comment: '


def add(cmd, execTime=None, comments={}):
	# type: (str, Union[None, int, float, datetime.datetime], Optional[Mapping[str, str]]) -> Optional[AtJob]
	"""
	Add a new command to the job queue given a time
	at which the job will be executed.

	:param execTime: execution time either as seconds since the epoch or as a :py:class:`datetime.datetime` instance. Defaults to `now`.
	:type execTime: int or float or datetime.datetime or None
	:param dict comments: A optional dictionary with comments to be associated with the job.
	:returns: The created job or `None`.
	:rtype: AtJob or None
	"""

	if isinstance(execTime, (int, float)):
		start = datetime.datetime.fromtimestamp(execTime)  # type: Optional[datetime.datetime]
	else:
		start = execTime

	# launch the at job directly
	atCmd = ['/usr/bin/at']
	if start:
		jobTime = start.strftime(_timeFormatWrite)
		jobDate = start.strftime(_dateFormatWrite)
		atCmd.extend([jobTime, jobDate])
	else:
		atCmd.append('now')

	# prevent injections from user supplied input
	# by encoding newlines
	def _encode_comment(value):
		if isinstance(value, bytes):
			try:
				value = value.decode('utf-8')
			except UnicodeDecodeError:
				value = value.decode('latin-1')
		return (u'%s' % (value,)).encode('unicode_escape').decode('ASCII')

	# add comments
	if comments:
		cmd = '\n'.join('%s%s:%s' % (COMMENT_PREFIX, _encode_comment(c[0]).replace(':', ''), _encode_comment(c[1])) for c in comments.items()) + '\n' + SCRIPT_PREFIX + '\n' + cmd

	# add job
	p = subprocess.Popen(atCmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

	# send the job to stdin
	out = p.communicate(cmd.encode('UTF-8'))

	# parse output and return job
	matches = _regJobNr.findall(b'\n'.join(out))
	if matches:
		return load(int(matches[0]))
	return None


def reschedule(nr, execTime=None):
	# type: (int, Optional[float]) -> Optional[AtJob]
	"""
	Re-schedules the at job with the given number for the specified time.

	:param int nr: The job number.
	:param execTime: execution time either as seconds since the epoch or as a :py:class:`datetime.datetime` instance. Defaults to `now`.
	:type execTime: int or float or datetime.datetime or None
	:returns: The created job or `None`.
	:rtype: AtJob or None
	:raises: AttributeError: if the job cannot be found.
	"""
	atjob = load(nr, extended=True)
	if atjob is None:
		raise AttributeError('Could not find at job %s' % nr)
	if atjob.command is None:
		raise AttributeError('The command of the at job is not available')
	atjob.rm()

	return add(atjob.command, execTime, atjob.comments)


def list(extended=False):
	# type: (bool) -> List[AtJob]
	"""
	Returns a list of all registered jobs.

	:param bool extended: If set to `True` also the comments and the command to execute are fetched.
	:returns: A list of :py:class:`AtJob` instances.
	:rtype: list[AtJob]

	This can be used to re-schedule a job.
	"""
	p = subprocess.Popen('/usr/bin/atq', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out = p.communicate()[0].decode('UTF-8', 'replace').splitlines()
	jobs = []
	for line in out:
		ijob = _parseJob(line)
		if ijob:
			jobs.append(ijob)

	if extended:
		for job in jobs:
			_parseScript(job)

	return jobs


def load(nr, extended=False):
	# type: (int, bool) -> Optional[AtJob]
	"""
	Load the job given.

	:param nr: Job number.
	:param bool extended: If set to `True` also the comments and the command to execute are fetched.
	:returns: `None` if job does not exist, otherwise an instance of :py:class:`AtJob`.
	:rtype: AtJob
	"""
	result = [p for p in list(extended) if p.nr == nr]
	if len(result):
		return result[0]
	return None


def remove(nr):
	# type: (int) -> Optional[int]
	"""
	Removes the at job with the given number.

	:param int nr: Job number.
	"""
	for job in list():
		if job.nr == nr:
			return job.rm()
	return None


def _parseScript(job):
	# type: (AtJob) -> None
	"""
	Internal function to load the job details by parsing the job of :command:`atq`.

	:param AtJob job: A job.
	"""
	# FIXME: This should be a method of the class.
	p = subprocess.Popen(['/usr/bin/at', '-c', str(job.nr)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out = p.communicate()[0].decode('UTF-8', 'replace').splitlines()
	job.comments = {}
	script = False
	job.command = ''
	for line in out:
		if script:
			job.command = '%s%s\n' % (job.command, line)
			continue
		if line.startswith(COMMENT_PREFIX):
			line = line[len(COMMENT_PREFIX):]
			try:
				key, value = line.split(':', 1)
			except ValueError:
				continue
			try:
				key, value = key.encode('UTF-8').decode('unicode_escape'), value.encode('UTF-8').decode('unicode_escape')
			except UnicodeDecodeError:
				pass  # can only happen if user manipulates/fakes atjob.
			job.comments[key] = value
		elif line.startswith(SCRIPT_PREFIX):
			script = True


def _parseJob(string):
	# type: (str) -> Optional[AtJob]
	"""
	Internal method to parse output of :command:`atq`.

	:param str string: A output line of :command:`atq`.
	:returns: A :py:class:`AtJob` instance or `None`
	:rtype: AtJob
	"""
	timeLocale = locale.getlocale(locale.LC_TIME)
	try:
		# change the time locale temporarily to 'C' as atq uses English date format
		# ignoring the currently set locale
		locale.setlocale(locale.LC_TIME, 'C')

		# parse string
		tmp = _regWhiteSpace.split(string)
		execTime = datetime.datetime.strptime(' '.join(tmp[1:6]), _dateTimeFormatRead)
		isRunning = tmp[6] == '='
		owner = tmp[7]
		nr = int(tmp[0])
	except (IndexError, ValueError):
		# parsing failed
		return None
	finally:
		# reset locale to default
		locale.setlocale(locale.LC_TIME, timeLocale)

	return AtJob(nr, owner, execTime, isRunning)


class AtJob(object):
	"""
	This class is an abstract representation of an at-job. Do not initiate
	the class directly, but use the methods provided in this module.

	:param int nr: Job number.
	:param str owner: User owning the job.
	:param datetime.datetime execTime: Planned job execution time.
	:param bool isRunning: `True` is the jub is currently running, `False` otherwise.
	"""
	def __init__(self, nr, owner, execTime, isRunning):
		# type: (int, str, datetime.datetime, bool) -> None
		self.nr = nr
		self.owner = owner
		self.command = None  # type: Optional[str]
		self.execTime = execTime
		self.isRunning = isRunning
		self.comments = {}  # type: Dict[str, str]

	def __str__(self):
		# type: () -> str
		t = self.execTime.strftime(_dateTimeFormatWrite)
		if self.isRunning:
			t = 'running'
		return 'Job #%d (%s)' % (self.nr, t)

	def __repr__(self):
		# type: () -> str
		return self.__str__()

	def rm(self):
		# type: () -> int
		"""
		Remove the job from the queue.
		"""
		p = subprocess.Popen(['/usr/bin/atrm', str(self.nr)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		p.communicate()
		return p.returncode == 0
