#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  appcenter logging module
#
# Copyright 2015 Univention GmbH
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

import logging
import sys

LOG_FILE = '/var/log/univention/appcenter.log'

def get_base_logger():
	return logging.getLogger('univention.appcenter')

class RangeFilter(logging.Filter):
	def __init__(self, min_level=None, max_level=None):
		self.min_level = min_level
		self.max_level = max_level

	def filter(self, record):
		if self.max_level is None:
			return record.levelno >= self.min_level
		if self.min_level is None:
			return record.levelno <= self.max_level
		return self.min_level <= record.levelno <= self.max_level

class UMCHandler(logging.Handler):
	def emit(self, record):
		try:
			from univention.management.console.log import MODULE
		except ImportError:
			pass
		else:
			msg = str(self.format(record))
			if record.level <= logging.DEBUG:
				MODULE.info(msg)
			elif record.level <= logging.INFO:
				MODULE.process(msg)
			elif record.level <= logging.WARN:
				MODULE.warn(msg)
			else:
				MODULE.error(msg)

def _reverse_umc_module_logger(exclusive=True):
	try:
		from univention.management.console.log import MODULE
	except ImportError:
		pass
	else:
		logger = MODULE._fallbackLogger
		if exclusive:
			for handler in logger.handlers:
				logger.removeHandler(handler)
		logger.parent = get_base_logger()

_logging_to_stream = False
def log_to_stream():
	global _logging_to_stream
	if not _logging_to_stream:
		_logging_to_stream = True
		logger = get_base_logger()
		handler = logging.StreamHandler(sys.stdout)
		handler.addFilter(RangeFilter(min_level=logging.INFO, max_level=logging.INFO))
		logger.addHandler(handler)
		handler = logging.StreamHandler(sys.stderr)
		formatter = logging.Formatter('\x1b[1;31m%(message)s\x1b[0m') # red
		handler.setFormatter(formatter)
		handler.addFilter(RangeFilter(min_level=logging.WARN))
		logger.addHandler(handler)

class ShortNameFormatter(logging.Formatter):
	shorten = get_base_logger().name

	def format(self, record):
		record.short_name = record.name
		if record.short_name.startswith('%s.' % self.shorten):
			record.short_name = record.short_name[len(self.shorten) + 1:]
		return super(ShortNameFormatter, self).format(record)

_logging_to_logfile = False
def log_to_logfile():
	global _logging_to_logfile
	if not _logging_to_logfile:
		_logging_to_logfile = True
		log_format = '%(process)6d %(short_name)-32s %(asctime)s: %(message)s'
		log_format_time = '%y-%m-%d %H:%M:%S'
		formatter = ShortNameFormatter(log_format, log_format_time)
		handler = logging.FileHandler(LOG_FILE)
		handler.setFormatter(formatter)
		get_base_logger().addHandler(handler)

get_base_logger().setLevel(logging.DEBUG)

