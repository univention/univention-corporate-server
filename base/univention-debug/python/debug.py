#!/usr/bin/python2.4
#
# Univention Debug
#  debug.py
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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

import univention.utf8
import _debug
from _debug import *

def debug(id, level, ustring, utf8=1):
	try:
		if utf8:
			string=univention.utf8.encode(ustring)
		else:
			string=ustring
		_debug.debug(id, level, string)
	except:
		pass

class function:
	def __init__(self, text,  utf8=1):
		try:
			if utf8:
				self.text=univention.utf8.encode(text)
			else:
				self.text=text
			_debug.begin(self.text)
		except:
			pass
	def __del__(self):
		try:
			_debug.end(self.text)
		except:
			pass
