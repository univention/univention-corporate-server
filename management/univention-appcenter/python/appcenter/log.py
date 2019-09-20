#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  appcenter logging module
#
# Copyright 2015-2019 Univention GmbH
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
'''
Univention App Center library:
	Logging module

The library logs various messages to logger objects (python stdlib logging)
univention.appcenter.log defines the appcenter base logger, as well as
functions to link the logger objects to the application using the library.

>>> from univention.appcenter.log import *

>>> log_to_logfile()
>>> # logs all messages to '/var/log/univention/appcenter.log'

>>> log_to_stream()
>>> # logs messages other than debug to stdout or (warning/error) stderr

>>> base_logger = get_base_logger()
>>> base_logger.info('This is an info message')
>>> base_logger.warn('And this is a warning')
'''

import logging
import sys
from contextlib import contextmanager

LOG_FILE = '/var/log/univention/appcenter.log'


def get_base_logger():
	'''Returns the base logger for univention.appcenter'''
	return logging.getLogger('univention.appcenter')


class RangeFilter(logging.Filter):

	'''A Filter object that filters messages in a certain
	range of logging levels'''

	def __init__(self, min_level=None, max_level=None):
		super(RangeFilter, self).__init__()
		self.min_level = min_level
		self.max_level = max_level

	def filter(self, record):
		if self.max_level is None:
			return record.levelno >= self.min_level
		if self.min_level is None:
			return record.levelno <= self.max_level
		return self.min_level <= record.levelno <= self.max_level


class UMCHandler(logging.Handler):

	'''Handler to link a logger to the UMC logging mechanism'''

	def emit(self, record):
		try:
			from univention.management.console.log import MODULE
		except ImportError:
			pass
		else:
			msg = str(self.format(record))
			if record.levelno <= logging.DEBUG:
				MODULE.info(msg)
			elif record.levelno <= logging.INFO:
				MODULE.process(msg)
			elif record.levelno <= logging.WARN:
				MODULE.warn(msg)
			else:
				MODULE.error(msg)


class StreamReader(object):

	def __init__(self, logger, level):
		self.logger = logger
		self.level = level

	def write(self, msg):
		if self.logger:
			self.logger.log(self.level, msg.rstrip('\n'))

	def flush(self):
		pass


class LogCatcher(object):

	def __init__(self, logger=None):
		self._original_name = None
		self.logger = logger
		if logger:
			self._original_name = logger.name
		self.logs = []

	def getChild(self, name):
		if self.logger:
			self.logger.name = '%s.%s' % (self.logger.name, name)
		return self

	def __del__(self):
		if self.logger and self._original_name:
			self.logger.name = self._original_name

	def debug(self, msg):
		if self.logger:
			self.logger.debug(msg)

	def info(self, msg):
		if self.logger:
			self.logger.info(msg)
		self.logs.append(('OUT', msg))

	def warn(self, msg):
		if self.logger:
			self.logger.warn(msg)
		self.logs.append(('ERR', msg))

	def fatal(self, msg):
		if self.logger:
			self.logger.warn(msg)
		self.logs.append(('ERR', msg))

	def has_stdout(self):
		return any(self.stdout())

	def has_stderr(self):
		return any(self.stderr())

	def stdout(self):
		for level, msg in self.logs:
			if level == 'OUT':
				yield msg

	def stderr(self):
		for level, msg in self.logs:
			if level == 'ERR':
				yield msg

	def stdstream(self):
		for level, msg in self.logs:
			yield msg


def _reverse_umc_module_logger(exclusive=True):
	'''Function to redirect UMC logs to the univention.appcenter logger.
	Useful when using legacy code when the App Center lib was part of the
	UMC module
	'''
	try:
		from univention.management.console.log import MODULE
	except ImportError:
		pass
	else:
		logger = MODULE._fallbackLogger  # pylint: disable=protected-access
		if exclusive:
			for handler in logger.handlers:
				logger.removeHandler(handler)
		logger.parent = get_base_logger()


@contextmanager
def catch_stdout(logger=None):
	'''Helper function to redirect stdout output to a logger. Or, if not
	given, suppress completely. Useful when calling other libs that do not
	use logging, instead just print statements.
	'''
	old_stdout = sys.stdout
	old_stderr = sys.stderr
	sys.stdout = StreamReader(logger, logging.INFO)
	sys.stderr = StreamReader(logger, logging.WARN)
	try:
		yield
	finally:
		sys.stdout = old_stdout
		sys.stderr = old_stderr


def log_to_stream():
	'''Call this function to log to stdout/stderr
	stdout: logging.INFO
	stderr: logging.WARN and upwards
	logging.DEBUG: suppressed
	only the message is logged, no further formatting
	stderr is logged in red (if its a tty)
	'''
	if not log_to_stream._already_set_up:
		log_to_stream._already_set_up = True
		logger = get_base_logger()
		handler = logging.StreamHandler(sys.stdout)
		handler.addFilter(RangeFilter(min_level=logging.INFO, max_level=logging.INFO))
		logger.addHandler(handler)
		handler = logging.StreamHandler(sys.stderr)
		if sys.stderr.isatty():
			formatter = logging.Formatter('\x1b[1;31m%(message)s\x1b[0m')  # red
			handler.setFormatter(formatter)
		handler.addFilter(RangeFilter(min_level=logging.WARN))
		logger.addHandler(handler)


log_to_stream._already_set_up = False


class ShortNameFormatter(logging.Formatter):

	'''Simple formatter to cut out unneeded bits of the logger's name'''
	shorten = get_base_logger().name

	def format(self, record):
		record.short_name = record.name
		if record.short_name.startswith('%s.' % self.shorten):
			record.short_name = record.short_name[len(self.shorten) + 1:]
		return super(ShortNameFormatter, self).format(record)


def get_logfile_logger(name):
	mylogger = logging.getLogger(name)
	mylogger.handlers = list()
	log_format = '%(process)6d %(short_name)-32s %(asctime)s [%(levelname)8s]: %(message)s'
	log_format_time = '%y-%m-%d %H:%M:%S'
	formatter = ShortNameFormatter(log_format, log_format_time)
	handler = logging.FileHandler(LOG_FILE)
	handler.setFormatter(formatter)
	mylogger.addHandler(handler)
	mylogger.setLevel(logging.DEBUG)
	return mylogger

def log_to_logfile():
	'''Call this function to log to /var/log/univention/appcenter.log
	Needs rights to write to it (i.e. should be root)
	Formats the message so that it can be analyzed later (i.e. process id)
	Logs DEBUG as well
	'''
	if not log_to_logfile._already_set_up:
		log_to_logfile._already_set_up = True
		log_format = '%(process)6d %(short_name)-32s %(asctime)s [%(levelname)8s]: ' \
			'%(message)s'
		log_format_time = '%y-%m-%d %H:%M:%S'
		formatter = ShortNameFormatter(log_format, log_format_time)
		handler = logging.FileHandler(LOG_FILE)
		handler.setFormatter(formatter)
		get_base_logger().addHandler(handler)


log_to_logfile._already_set_up = False

get_base_logger().setLevel(logging.DEBUG)
get_base_logger().addHandler(logging.NullHandler())  # this is to prevent warning messages
