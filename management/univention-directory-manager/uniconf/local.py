# -*- coding: utf-8 -*-
#
# Univention Diectory Manager
#  translation basics
#
# Copyright (C) 2004, 2005, 2006, 2007 Univention GmbH
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

class LazyTranslation (str):
	'''
	NOTE this class exists in:

	univention-directory-manager/uniconf/local.py
		this file contains also test cases for allmost all functions
	univention-direcotry-manager-modules/modules/univention/admin/localization.py
	univention-webui/modules/localwebui.py
	univention-management-console/modules/univention/management/console/locales.py
	'''
	def __init__ (self, string):
		self._domain = None
		self._orig_str = string.__str__ ()
		self._translations = {}
		super (str, self).__init__ (self._orig_str)

	def __add__(self, y):
		return str (self) + str (y)

	def __contains__(self, y):
		return str (y) in str (self)

	def __eq__(self, y):
		return str (self) == str (y)

	def __ge__(self, y):
		return str (self) >= str (y)

	def __getitem__(self, y):
		return str (self)[y]

	def __getslice__(self, i, j):
		return str (self)[i:j]

	def __gt__(self, y):
		return str (self) > str (y)

	def __le__(self, y):
		return str (self) <= str (y)

	def __len__(self):
		return len (str (self))

	def __lt__(self, y):
		return str (self) < str (y)

	def __mul__(self, n):
		return str (self) * n

	def __rmul__(self, n):
		return n * str (self)

	def __ne__(self, y):
		return str (self) != str (y)

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
			newval = t.ugettext(self._orig_str)
		else:
			newval = self._orig_str
		self._translations[lang] = newval
		return newval

	def __repr__ (self):
		return "'%s'" % self.__str__ ()

	def capitalize(self):
		return str (self).capitalize ()

	def center(self, width, fillchar=' '):
		return str (self).center (width, fillchar)

	def count(self, sub, start=0, end=-1):
		return str (self).count (sub, start, end)

	def decode(self, encoding=None, error=None):
		if encoding != None:
			if error != None:
				return str (self).decode (encoding, error)
			return str (self).decode (encoding)
		return str (self).decode ()

	def encode(self, encoding=None, error=None):
		if encoding != None:
			if error != None:
				return str (self).encode (encoding, error)
			return str (self).encode (encoding)
		return str (self).encode ()

	def endswith(self, suffix, start=0, end=None):
		if end != None:
			return str (self).endswith (suffix, start, end)
		return str (self).endswith (suffix, start)

	def expandtabs(self, tabsize=8):
		return str (self).expandtabs (tabsize)

	def find(self, sub, start=0, end=-1):
		return str (self).find (sub, start, end)

	def index(self, sub, start=0, end=-1):
		return str (self).index (sub, start, end)

	def isalnum(self):
		return str (self).isalnum ()

	def isalpha(self):
		return str (self).isalpha ()

	def isdigit(self):
		return str (self).isdigit ()

	def islower(self):
		return str (self).islower ()

	def isspace(self):
		return str (self).isspace ()

	def istitle(self):
		return str (self).istitle ()

	def isupper(self):
		return str (self).isupper ()

	def join(self, sequence):
		return str (self).join (sequence)

	def ljust(self, width, fillchar=' '):
		return str (self).ljust (width, fillchar)

	def lower(self):
		return str (self).lower ()

	def lstrip(self, chars=0):
		if chars != 0:
			return str (self).lstrip (chars)
		return str (self).lstrip ()

	def replace(self, old, new, count=-1):
		if count != -1:
			return str (self).replace (old, new, count)
		return str (self).replace (old, new)

	def rfind(self, sub, start=0, end=-1):
		return str (self).rfind (sub, start, end)

	def rindex(self, sub, start=0, end=-1):
		return str (self).rindex (sub, start, end)

	def rjust(self, width, fillchar=' '):
		return str (self).rjust (width, fillchar)

	def rsplit(self, sep=' ', maxsplit=-1):
		if maxsplit != -1:
			return str (self).rsplit (sep, maxsplit)
		return str (self).rsplit (sep)

	def rstrip(self, chars=0):
		if chars != 0:
			return str (self).rstrip (chars)
		return str (self).rstrip ()

	def split(self, sep=' ', maxsplit=-1):
		if maxsplit != -1:
			return str (self).split (sep, maxsplit)
		return str (self).split (sep)

	def splitlines(self, keepends=False):
		return str (self).splitlines (keepends)

	def startswith(self, prefix, start=0, end=-1):
		return str (self).startswith (prefix, start, end)

	def strip(self, chars=0):
		if chars != 0:
			return str (self).strip (chars)
		return str (self).strip ()

	def swapcase(self):
		return str (self).swapcase ()

	def title(self):
		return str (self).title ()

	def translate(self, table, deletechars=None):
		if deletechars:
			return str (self).translate (table, deletechars)
		return str (self).translate (table)

	def upper(self):
		return str (self).upper ()

	def zfill(self, width):
		return str (self).zfill (width)

def _(val):
	t = LazyTranslation (val)
	t._domain = "univention-directory-manager-webfrontend"
	return t

def lazyTranslationTest ():
	'''
	To run the following test, you have to add:
	return 'bla blub'

	as the first line of function LazyTranslation.__str__.
	Don't forget to remove the line after you finished the tests ;-)
	'''
	y = 'bla blub'
	x = _('foo bar')

	#print x + y
	#print y + x
	#assert x + y == y + x # test failed
	#print x in y
	#assert x in y # test failed
	assert y in x
	assert x == y
	assert x >= y
	assert (x >= y + 'a') == False
	assert x[1] == y[1]
	assert x[-1] == y[-1]
	assert x[1:3] == y[1:3]
	assert x >= y
	assert x <= y
	assert len(x) == len(y)
	assert (x < y) == False
	assert '%s' % x == '%s' % y
	assert x * 3 == y * 3
	assert (x != y) == False
	assert repr (x) == repr (y)
	#x.__rmod__(<++>) # no test for this case
	assert 3 * x == 3 * y
	assert str (x) == str (y)
	assert x.capitalize() == y.capitalize()
	assert x.center(80)       == y.center(80)
	assert x.count('a')       == y.count('a')
	assert x.decode('utf-8')  == y.decode('utf-8')
	assert x.encode('utf-8')  == y.encode('utf-8')
	assert x.endswith('blub') == y.endswith('blub')
	assert x.expandtabs()     == y.expandtabs()
	assert x.find('a')        == y.find('a')
	assert x.index('a')       == y.index('a')
	assert x.isalnum()        == y.isalnum()
	assert x.isalpha()        == y.isalpha()
	assert x.isdigit()        == y.isdigit()
	assert x.islower()        == y.islower()
	assert x.isspace()        == y.isspace()
	assert x.istitle()        == y.istitle()
	assert x.isupper()        == y.isupper()
	assert x.join([' nee'])   == y.join([' nee'])
	assert x.ljust(80)        == y.ljust(80)
	assert x.lower()          == y.lower()
	assert x.lstrip()         == y.lstrip()
	assert x.replace('a', 'b')== y.replace('a', 'b')
	assert x.rfind('a')       == y.rfind('a')
	assert x.rindex('a')      == y.rindex('a')
	assert x.rjust(80)        == y.rjust(80)
	assert x.rsplit()         == y.rsplit()
	assert x.rstrip()         == y.rstrip()
	assert x.split()          == y.split()
	assert x.splitlines()     == y.splitlines()
	assert x.startswith('bla')== y.startswith('bla')
	assert x.strip()          == y.strip()
	assert x.swapcase()       == y.swapcase()
	assert x.title()          == y.title()
	#assert x.translate()     == y.translate()
	assert x.upper()          == y.upper()
	assert x.zfill(80)        == y.zfill(80)

	class b:
		def __str__ (self):
			return _('blub')
	assert str (b ()) == y
	assert _(b ()) == y

if __name__ == '__main__':
	lazyTranslationTest ()
