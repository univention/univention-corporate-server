#
# Univention Python
#  UTF-8 helper functions
#
# Copyright 2002-2010 Univention GmbH
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

import codecs
import types
import sys

(utf8_encode,utf8_decode,utf8_reader,utf8_writer)=codecs.lookup('utf-8')
(iso_encode,iso_decode,isoblar,isoblaw)=codecs.lookup('iso-8859-1')

def decode(ob, ignore=[]):
	if ob == None:
		return ob
	if isinstance(ob,types.StringType) or isinstance(ob,types.UnicodeType):
		return utf8_decode(ob)[0]
	if isinstance(ob,types.ListType):
		ls=[]
		for i in ob:
			ls.append(decode(i, ignore))
		return ls
	if isinstance(ob,types.TupleType):
		return tuple(decode(list(ob), ignore))
	if isinstance(ob,types.DictType):
		dict={}
		for k in ob.keys():
			if k in ignore:
				dict[k]=ob[k]
			else:
				dict[k]=decode(ob[k], ignore)
		return dict

def encode(ob):
	if ob == None:
		return ob
	if isinstance(ob,types.StringType) or isinstance(ob,types.UnicodeType):
		try:
			return utf8_encode(ob)[0]
		except Exception,ex:
			if isinstance(ob,types.StringType):
				return utf8_encode(ob)[0]

	if isinstance(ob,types.ListType):
		ls=[]
		for i in ob:
			ls.append(encode(i))
		return ls
	if isinstance(ob,types.TupleType):
		return tuple(encode(list(ob)))
	if isinstance(ob,types.DictType):
		dict={}
		for k in ob.keys():
			dict[k]=encode(ob[k])
		return dict
	else:
		return ob
