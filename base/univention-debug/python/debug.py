#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Debug
#  debug.py
#
# Copyright 2004-2014 Univention GmbH
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
"""Univention debugging and logging library.

example:

>>> import univention.debug as ud
>>> ud.init("stdout", ud.NO_FLUSH, ud.FUNCTION) #doctest: +ELLIPSIS
... ...  DEBUG_INIT
>>> ud.set_level(ud.LISTENER, ud.ERROR)
>>> ud.debug(ud.LISTENER, ud.ERROR, 'Fatal error: var=%s' % 42) #doctest: +ELLIPSIS
... ...  LISTENER    ( ERROR   ) : Fatal error: var=42
"""

import _debug
from _debug import *

def debug(id, level, ustring, utf8=True):
	_debug.debug(id, level, ustring)

class function:
	def __init__(self, text, utf8=True):
		self.text = text
		_debug.begin(self.text)

	def __del__(self):
		_debug.end(self.text)

if __name__ == '__main__':
	import doctest
	doctest.testmod()
