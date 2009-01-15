# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  localization
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

import univention.debug
import gettext, os

'''
usage:
translation=univention.admin.localization.translation()
_=translation.translate
'''
import locale

class LazyTranslation (str):
	'''
	NOTE this class exists in univention-directory-manager local.py
	and univention-direcotry-manager-modules localization.py
	'''
	def __init__ (self, string):
		self._domain = None
		self.__orig_str = str (string)
		self._translations = {}
		super (str, self).__init__ (self.__orig_str)
	def __mod__ (self, y):
		return str(self) % y
	def __rmod__ (self, x):
		return x % str(self)
	def __str__ (self):
		lang = locale.getlocale( locale.LC_MESSAGES )
		if self._translations.has_key (lang):
			return self._translations[lang]
		if lang and lang[0] and \
				self._domain != None and gettext.find (self._domain, languages=(lang[0], )):
			t = gettext.translation(self._domain, languages=(lang[0], ))
			newval = t.ugettext(self.__orig_str)
		else:
			newval = self.__orig_str
		self._translations[lang] = newval
		return newval
	def __repr__ (self):
		return self.__str__ ()

class translation:
	def __init__( self, namespace ):
		self.domain = namespace.replace( '/', '-' ).replace( '.', '-' )

	def translate( self, message ):
		t = LazyTranslation (message)
		t._domain = self.domain
		return t

