# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  samba related code
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

import string
import types

class acctFlags:
	def __init__(self, flagstring=None, flags=None, fallbackflags=None):
		if flags is not None:
			self.__flags=flags
			return
		if not flagstring or not isinstance(flagstring, types.StringTypes) or len(flagstring)!=13:
			if fallbackflags != None:
				self.__flags=fallbackflags
				return
			flagstring="[U          ]"
		flags={}
		flagstring=flagstring[1:-1]
		for letter in flagstring:
			if not letter in string.whitespace:
				flags[letter]=1
		self.__flags=flags
	
	def __setitem__(self, key, value):
		self.__flags[key]=value
	
	def __getitem__(self, key):
		return self.__flags[key]

	def decode(self):
		flagstring="["
		for flag, set in self.__flags.items():
			if set:
				flagstring=flagstring+flag
		while len(flagstring)<12:
			flagstring+=" "
		flagstring+="]"
		return flagstring

	def set(self, flag):
		self[flag]=1
		return self.decode()

	def unset(self, flag):
		self[flag]=0
		return self.decode()

