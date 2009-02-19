# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  localization
#
# Copyright (C) 2004-2009 Univention GmbH
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

import gettext
import locale
import sys
from types import StringTypes

'''
usage:
translation=univention.admin.localization.translation()
_=translation.translate
'''

class LazyTranslation (str):
	'''
	NOTE this class exists in:

	univention-directory-manager/uniconf/local.py
		this file contains also test cases for allmost all functions
	univention-directory-manager-modules/modules/univention/admin/localization.py
	univention-webui/modules/localwebui.py
	univention-management-console/modules/univention/management/console/locales.py
	'''
	def __init__(self, seq):
		self._domain = None
		self._translations = {}

		if isinstance(seq, StringTypes):
			self.data = seq
		elif isinstance(seq, LazyTranslation):
			self.data = seq.data[:]
		else:
			self.data = '%s' % seq
		super (str, self).__init__ (self.data)
	def __str__ (self):
		newval = ''
		lang = locale.getlocale( locale.LC_MESSAGES )
		if self._translations.has_key (lang):
			return self._translations[lang]
		if lang and lang[0] and \
				self._domain != None and gettext.find (self._domain, languages=(lang[0], )):
			t = gettext.translation(self._domain, languages=(lang[0], ))
			newval = t.ugettext(self.data)
		else:
			newval = self.data
		self._translations[lang] = newval
		return newval
	def __repr__(self): return "'%s'" % self
	def __int__(self): return int(str (self))
	def __long__(self): return long( str(self))
	def __float__(self): return float(str (self))
	def __complex__(self): return complex(str (self))
	def __hash__(self): return hash(str (self))

	def __cmp__(self, string):
		if isinstance(string, LazyTranslation):
			return cmp(str (self), str (string))
		else:
			return cmp(str (self), string)
	def __contains__(self, char):
		return char in str (self)

	def __len__(self): return len(str (self))
	def __getitem__(self, index): return str (self)[index]
	def __getslice__(self, start, end):
		start = max(start, 0); end = max(end, 0)
		return str (self)[start:end]

	def __add__(self, other):
		if isinstance(other, LazyTranslation):
			return str (self) + str (other)
		elif isinstance(other, StringTypes):
			return str (self) + other
		else:
			return str (self) + str(other)
	def __radd__(self, other):
		if isinstance(other, StringTypes):
			return other + str (self)
		else:
			return str(other) + str (self)
	def __mul__(self, n):
		return str (self)*n
	__rmul__ = __mul__
	def __mod__(self, args):
		return str (self) % args

	def __eq__(self, other):
		return str (self) == str (other)

	def __ge__(self, other):
		return str (self) >= str (other)

	def __gt__(self, other):
		return str (self) > str (other)

	def __le__(self, other):
		return str (self) <= str (other)

	def __lt__(self, other):
		return str (self) < str (other)

	def __ne__(self, other):
		return str (self) != str (other)

	# the following methods are defined in alphabetical order:
	def capitalize(self): return str (self).capitalize()
	def center(self, width, *args):
		return str (self).center(width, *args)
	def count(self, sub, start=0, end=sys.maxint):
		return str (self).count(sub, start, end)
	def decode(self, encoding=None, errors=None): # XXX improve this?
		if encoding:
			if errors:
				return str (self).decode(encoding, errors)
			else:
				return str (self).decode(encoding)
		else:
			return str (self).decode()
	def encode(self, encoding=None, errors=None): # XXX improve this?
		if encoding:
			if errors:
				return str (self).encode(encoding, errors)
			else:
				return str (self).encode(encoding)
		else:
			return str (self).encode()
	def endswith(self, suffix, start=0, end=sys.maxint):
		return str (self).endswith(suffix, start, end)
	def expandtabs(self, tabsize=8):
		return str (self).expandtabs(tabsize)
	def find(self, sub, start=0, end=sys.maxint):
		return str (self).find(sub, start, end)
	def index(self, sub, start=0, end=sys.maxint):
		return str (self).index(sub, start, end)
	def isalpha(self): return str (self).isalpha()
	def isalnum(self): return str (self).isalnum()
	def isdecimal(self): return str (self).isdecimal()
	def isdigit(self): return str (self).isdigit()
	def islower(self): return str (self).islower()
	def isnumeric(self): return str (self).isnumeric()
	def isspace(self): return str (self).isspace()
	def istitle(self): return str (self).istitle()
	def isupper(self): return str (self).isupper()
	def join(self, seq): return str (self).join(seq)
	def ljust(self, width, *args):
		return str (self).ljust(width, *args)
	def lower(self): return str (self).lower()
	def lstrip(self, chars=None): return str (self).lstrip(chars)
	def replace(self, old, new, maxsplit=-1):
		return str (self).replace(old, new, maxsplit)
	def rfind(self, sub, start=0, end=sys.maxint):
		return str (self).rfind(sub, start, end)
	def rindex(self, sub, start=0, end=sys.maxint):
		return str (self).rindex(sub, start, end)
	def rjust(self, width, *args):
		return str (self).rjust(width, *args)
	def rstrip(self, chars=None): return str (self).rstrip(chars)
	def split(self, sep=None, maxsplit=-1):
		return str (self).split(sep, maxsplit)
	def rsplit(self, sep=None, maxsplit=-1):
		return str (self).rsplit(sep, maxsplit)
	def splitlines(self, keepends=0): return str (self).splitlines(keepends)
	def startswith(self, prefix, start=0, end=sys.maxint):
		return str (self).startswith(prefix, start, end)
	def strip(self, chars=None): return str (self).strip(chars)
	def swapcase(self): return str (self).swapcase()
	def title(self): return str (self).title()
	def translate(self, *args):
		return str (self).translate(*args)
	def upper(self): return str (self).upper()
	def zfill(self, width): return str (self).zfill(width)

class translation:
	def __init__( self, namespace ):
		self.domain = namespace.replace( '/', '-' ).replace( '.', '-' )

	def translate( self, message ):
		t = LazyTranslation (message)
		t._domain = self.domain
		return t

