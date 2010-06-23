#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  reboot module: revamp module command result for the specific user interface
#
# Copyright 2008-2010 Univention GmbH
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

import os

import univention.management.console as umc
import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp
import univention.management.console.tools as umct

import univention.debug as ud

_ = umc.Translation( 'univention.management.console.handlers.reboot' ).translate

class Web( object ):
	def _web_raw_do(self,object,res):
		try:
			fn = object.options.get('file')
			data = open(fn,'r').read()
			res.dialog = { 'Content-Type': object.options.get('type'),
						   'Content': data }
		except:
			res.dialog = 'Hat nicht geklappt'
		self.revamped( object.id(), res, rawresult = True )

	def _web_raw_startup(self,object,res):
		lst = umcd.List()
		lst.add_row( [ umcd.HTML('<a href="ajax.py?session_id=%s&umcpcmd=raw/test/cmd&file=/etc/fstab&type=text/plain" target="_new">/etc/fstab</a>' % self._sessionid ) ] )
		lst.add_row( [ umcd.HTML('<a href="ajax.py?session_id=%s&umcpcmd=raw/test/cmd&file=/usr/share/icons/crystalsvg/64x64/devices/tablet.png&type=image/png" target="_new">PNG-File</a>'  % self._sessionid ) ] )
		res.dialog = lst
		self.revamped( object.id(), res )
