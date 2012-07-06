#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  helper functions for i18n
#
# Copyright 2004-2012 Univention GmbH
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

import gettext

def debug(text, file='/tmp/installer.log'):
	"""Log test to file."""
	f = open(file, 'a+')
	try:
		print >>f, text
	finally:
		f.close()

def _(val):
	"""
	Translate val according to current locale.

	>>> import locale; l = locale.setlocale(locale.LC_MESSAGES, 'de_DE.UTF-8')
	>>> _('Next')
	'Weiter'
	>>> t = 'Untranslated 123'; _(t)
	'Untranslated 123'
	"""
	for p in ('/lib/univention-installer/locale', 'locale'):
		try:
			t = gettext.translation('installer', p)
		except IOError, e:
			continue
		newval = t.gettext(val)
		return newval
	if _.__once:
		_.__once = False
		debug("No 'installer' locale found")
	return val
_.__once = True

if __name__ == '__main__':
	import doctest
	doctest.testmod()
