# -*- coding: utf-8 -*-
#
# Univention Management Console
#  i18n utils
#
# Copyright (C) 2006 Univention GmbH
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
import locale

'''
usage:
obj = univention.management.console.Translation()
_ = obj.translate
'''

class LazyTranslation (str):
	def __init__ (self, string):
		self._domain = None
		self.__orig_str = str (string)
		self._translations = {}
		super (str, self).__init__ (self.__orig_str)
	def __str__ (self):
		lang = locale.getlocale( locale.LC_MESSAGES )
		if self._translations.has_key (lang):
			return self._translations[lang]
		if lang and lang[0] and gettext.find (self._domain, languages=(lang[0], )):
			t = gettext.translation(self._domain, languages=(lang[0], ))
			newval = t.ugettext(self.__orig_str)
			self._translations[lang] = newval
		else:
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO,
					"no translation for %s (%s): %s" % (self.__orig_str, lang, self._domain))
			newval = self.__orig_str
		return str (newval)
	def __repr__ (self):
		return self.__str__ ()

class Translation:
	def __init__( self, namespace ):
		self._domain = namespace.replace( '/', '-' ).replace( '.', '-' )

	def translate( self, message ):
		t = LazyTranslation (message)
		t._domain = self._domain
		return t

