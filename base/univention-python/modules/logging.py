#!/usr/bin/python2.4
#
# Univention Python
#  logging functionality
#
# Copyright (C) 2002, 2003, 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import sys, time

class logging:
	def __init__(self):
		self.streams=[]
	def addStream(self, fd, minlevel, maxlevel, syntax, components=[]):
		"""
		adds stream fd to log to

		syntax string may contain:
		   %d  date
		   %m  message
		   %c  component
		   %l  level (numeric)
		   %L  level (string)
		"""
		self.streams.append((fd, minlevel, maxlevel, syntax, components))
	def _levelString(self, level):
		if level == 5:
			return 'DEBUG'
		elif level == 4:
			return 'INFO'
		elif level == 3:
			return 'NOTIFICATION'
		elif level == 2:
			return 'WARNING'
		elif level == 1:
			return 'ERROR'
	def message(self, component, level, message):
		date=time.ctime()
		level_string=self._levelString(level)
		for fd, minlevel, maxlevel, syntax, components in self.streams:
			if (components and not component in components) or minlevel > level or maxlevel < level:
				continue
			print >>fd, syntax.replace('%c', component).replace('%m', message).replace('%d', date).replace('%l', str(level)).replace('%L', level_string)
	def debug(self, component, message):
		self.message(component, 5, message)
	def info(self, component, message):
		self.message(component, 4, message)
	def notification(self, component, message):
		self.message(component, 3, message)
	def warning(self, component, message):
		self.message(component, 2, message)
	def error(self, component, message):
		self.message(component, 1, message)
