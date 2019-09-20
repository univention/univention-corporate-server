# -*- coding: utf-8 -*-
#
# Univention Python
#  UTF-8 helper functions
#
# Copyright 2002-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

import codecs

(utf8_encode, utf8_decode, utf8_reader, utf8_writer) = codecs.lookup('utf-8')
(iso_encode, iso_decode, iso_reader, iso_writer) = codecs.lookup('iso-8859-1')


def decode(ob, ignore=[]):
	u"""
	Decode object from UTF-8.

	>>> decode(None)
	>>> decode(chr(0xc3) + chr(0xa4)) == u'ä'
	True
	>>> decode([chr(0xc3) + chr(0xa4)]) == [u'ä']
	True
	>>> decode((chr(0xc3) + chr(0xa4),)) == (u'ä',)
	True
	>>> decode({42: chr(0xc3) + chr(0xa4)}) == {42: u'ä'}
	True
	>>> decode(set((chr(0xc3) + chr(0xa4),))) == set([u'ä'])
	True
	"""
	if ob is None:
		return ob
	elif isinstance(ob, basestring):
		return utf8_decode(ob)[0]
	elif isinstance(ob, list):
		return map(decode, ob)
	elif isinstance(ob, tuple):
		return tuple(map(decode, ob))
	elif isinstance(ob, set):
		return set(map(decode, ob))
	elif isinstance(ob, dict):
		d = {}
		for k, v in ob.items():
			if k in ignore:
				d[k] = v
			else:
				d[k] = decode(v, ignore)
		return d
	else:
		return ob


def encode(ob):
	u"""
	Encode object to UTF-8.

	>>> encode(None)
	>>> encode(u'ä')
	'\\xc3\\xa4'
	>>> encode([u'ä'])
	['\\xc3\\xa4']
	>>> encode((u'ä',))
	('\\xc3\\xa4',)
	>>> encode({42: u'ä'})
	{42: '\\xc3\\xa4'}
	>>> encode(set((u'ä',)))
	set(['\\xc3\\xa4'])
	"""
	if ob is None:
		return ob
	elif isinstance(ob, basestring):
		try:
			return utf8_encode(ob)[0]
		except Exception:
			return ob
	elif isinstance(ob, list):
		return map(encode, ob)
	elif isinstance(ob, tuple):
		return tuple(map(encode, ob))
	elif isinstance(ob, set):
		return set(map(encode, ob))
	elif isinstance(ob, dict):
		return dict(map(lambda k_v: (k_v[0], encode(k_v[1])), ob.items()))
	else:
		return ob


if __name__ == '__main__':
	# http://stackoverflow.com/questions/1733414/how-do-i-include-unicode-strings-in-python-doctests
	import sys
	reload(sys)
	sys.setdefaultencoding("UTF-8")
	import doctest
	doctest.testmod()
