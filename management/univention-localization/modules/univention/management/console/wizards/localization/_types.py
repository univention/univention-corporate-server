# -*- coding: utf-8 -*-
#
# Univention Management Console
#  baseconfig module: revamps dialog result for the web interface
#
# Copyright (C) 2006-2009 Univention GmbH
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

import univention.debug as ud
import univention.management.console as umc
import univention.management.console.dialog as umcd

_ = umc.Translation( 'univention.management.console.handlers.localization' ).translate

class DropDownBox( umc.StaticSelection ):
	def __init__( self , name, list=None):
		ud.debug( ud.ADMIN, ud.INFO, "FOOOTEST 123 - DropDownBox __init__ choices" )
		umc.StaticSelection.__init__( self, name )
		self._choices = list

	def set_choices(self,  list ):
		ud.debug( ud.ADMIN, ud.INFO, "FOOOTEST 123 - DropDownBox set_choices" )
		self._choices = list

	def choices( self ):
		ud.debug( ud.ADMIN, ud.INFO, "FOOOTEST 123 - DropDownBox choices " )
		ret = []
		for item in self._choices:
			if type([]) == type(item) and len(item) == 2:
				ret.append((item[1], item[0]))			
			elif type([]) != type(item):
				ret.append((item, item))
				
				
		return (tuple(ret))
umcd.copy( umc.StaticSelection, DropDownBox )

class MultiValueList( umc.MultiValue ):
	def __init__( self , name, list, required=False):
		umc.MultiValue.__init__( self, name, syntax=None)
		ud.debug( ud.ADMIN, ud.INFO, "FOOOTEST 123 - MultiValueList __init__ choices=%s" % list)
		self._choices = list

#	def set_choices(self,  list ):
#		ud.debug( ud.ADMIN, ud.INFO, "FOOOTEST 123 - MultiValueList set_choices=%s" % list)
#		self._choices = list

	def choices( self ):
		ud.debug( ud.ADMIN, ud.INFO, "FOOOTEST 123 - MultiValueList choices %s" % self._choices)
		ret = []
		for item in self._choices:
			if type([]) == type(item) and len(item) == 2:
				ret.append((item[1], item[0]))			
			elif type([]) != type(item):
				ret.append((item, item))
				
				
		return (tuple(ret))
	def is_valid(self, items):
		#the list should look like ['aa_DJ.UTF-8 UTF-8',...] and should not contain any double-dots (':')  because
		#they are used as escape charactes for the ucr variable 'locale'
		if not items:
			return True

		if type(items) != type([]):
			return False

		for item in items:
			if type(item) != type(''):
				return False
			if ':' in item:
				return False
		return True

umcd.copy( umc.StaticSelection, MultiValueList )


