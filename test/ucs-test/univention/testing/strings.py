# -*- coding: utf-8 -*-
#
# UCS test
#
# Copyright 2013-2019 Univention GmbH
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

import random

STR_NUMERIC = u'0123456789'
STR_ALPHA = u'abcdefghijklmnopqrstuvwxyz'
STR_ALPHANUM = STR_ALPHA + STR_NUMERIC
STR_ALPHANUMDOTDASH = STR_ALPHANUM + '.-'

STR_SPECIAL_CHARACTER = u'!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ ´€Ω®½'
STR_UMLAUT = u'äöüßâêôûŵẑŝĝĵŷĉ'
STR_UMLAUTNUM = STR_UMLAUT + STR_NUMERIC


def random_string(length=10, alpha=True, numeric=True, charset=None, encoding='utf-8'):
	"""
	Get specified number of random characters (ALPHA, NUMERIC or ALPHANUMERIC).
	Default is an alphanumeric string of 10 characters length. A custom character set
	may be defined via "charset" as string. The default encoding is UTF-8.
	If length is 0 or negative, an empty string is returned.
	"""
	result = u''
	for _ in range(length):
		if charset:
			result += random.choice(charset)
		elif alpha and numeric:
			result += random.choice(STR_ALPHANUM)
		elif alpha:
			result += random.choice(STR_ALPHA)
		elif numeric:
			result += random.choice(STR_NUMERIC)
	return result.encode(encoding)


def random_name(length=10):
	"""
	create random name (1 ALPHA, 8 ALPHANUM, 1 ALPHA)
	"""
	return random_string(length=1, alpha=True, numeric=False) + random_string(length=(length - 2), alpha=True, numeric=True) + random_string(length=1, alpha=True, numeric=False)


def random_name_special_characters(length=10):
	"""
	create random name (1 UMLAUT, 2 ALPHA, 6 SPECIAL_CHARACTERS + UMLAUT, 1 UMLAUTNUM)
	"""
	return '%s%s%s%s' % (
		random_string(length=1, alpha=False, numeric=False, charset=STR_UMLAUT),
		random_string(length=2, alpha=True, numeric=False),
		random_string(length=(length - 4), alpha=False, numeric=False, charset=STR_SPECIAL_CHARACTER + STR_UMLAUT),
		random_string(length=1, alpha=False, numeric=False, charset=STR_UMLAUTNUM)
	)


def random_username(length=10):
	return random_name(length)


def random_groupname(length=10):
	return random_name(length)


def random_int(bottom_end=0, top_end=9):
	return str(random.randint(bottom_end, top_end))


def random_version(elements=3):
	version = []
	for _ in range(elements):
		version.append(random_int(0, 9))
	return '.'.join(version)


def random_ucs_version(min_major=1, max_major=9, min_minor=0, max_minor=99, min_patchlevel=0, max_patchlevel=99):
	return '%s.%s-%s' % (random_int(min_major, max_major), random_int(min_minor, max_minor), random_int(min_patchlevel, max_patchlevel))


def random_mac():
	mac = [
		random.randint(0x00, 0x7f),
		random.randint(0x00, 0x7f),
		random.randint(0x00, 0x7f),
		random.randint(0x00, 0x7f),
		random.randint(0x00, 0xff),
		random.randint(0x00, 0xff)
	]

	return ':'.join(map(lambda x: "%02x" % x, mac))


# Generate 110 different ip addresses in the range 11.x.x.x-120.x.x.x
class IP_Iter(object):

	def __init__(self):
		self.max_range = 120
		self.index = 11

	def __iter__(self):
		return self

	def next(self):
		if self.index < self.max_range:
			ip_list = [
				self.index,
				random.randint(1, 254),
				random.randint(1, 254),
				random.randint(1, 254)
			]
			ip = ".".join(map(str, ip_list))
			self.index += 1
			return ip
		else:
			raise StopIteration()


def random_ip(ip_iter=IP_Iter()):
	return ip_iter.next()


def random_dns_record():
	# Bug #49679: the S4-Connector always appends a dot to nSRecord and ptrRecords without dot
	return '%s.' % (random_string(),)
