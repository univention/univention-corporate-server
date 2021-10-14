# -*- coding: utf-8 -*-
#
# UCS test
#
# Copyright 2013-2021 Univention GmbH
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

from random import choice, randint
from typing import Iterator, Text, Optional, Tuple  # noqa F401

import six

STR_NUMERIC = u'0123456789'
STR_ALPHA = u'abcdefghijklmnopqrstuvwxyz'
STR_ALPHANUM = STR_ALPHA + STR_NUMERIC
STR_ALPHANUMDOTDASH = STR_ALPHANUM + '.-'

STR_SPECIAL_CHARACTER = u'!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ ´€Ω®½'
STR_UMLAUT = u'äöüßâêôûŵẑŝĝĵŷĉ'
STR_UMLAUTNUM = STR_UMLAUT + STR_NUMERIC


def random_string(length=10, alpha=True, numeric=True, charset=u"", encoding='utf-8'):
	# type: (int, bool, bool, Text, str) -> str
	"""
	Get specified number of random characters (ALPHA, NUMERIC or ALPHANUMERIC).
	Default is an alphanumeric string of 10 characters length. A custom character set
	may be defined via "charset" as string. The default encoding is UTF-8.
	If length is 0 or negative, an empty string is returned.
	"""
	result = u''
	for _ in range(length):
		if charset:
			result += choice(charset)
		elif alpha and numeric:
			result += choice(STR_ALPHANUM)
		elif alpha:
			result += choice(STR_ALPHA)
		elif numeric:
			result += choice(STR_NUMERIC)
	if six.PY2:
		result = result.encode(encoding)
	return result


def random_name(length=10):
	# type: (int) -> str
	"""
	create random name (1 ALPHA, 8 ALPHANUM, 1 ALPHA)
	"""
	return ''.join((
		random_string(length=1, alpha=True, numeric=False),
		random_string(length=(length - 2), alpha=True, numeric=True),
		random_string(length=1, alpha=True, numeric=False),
	))


def random_name_special_characters(length=10):
	# type: (int) -> str
	"""
	create random name (1 UMLAUT, 2 ALPHA, 6 SPECIAL_CHARACTERS + UMLAUT, 1 UMLAUTNUM)
	"""
	return ''.join((
		random_string(length=1, alpha=False, numeric=False, charset=STR_UMLAUT),
		random_string(length=2, alpha=True, numeric=False),
		random_string(length=(length - 4), alpha=False, numeric=False, charset=STR_SPECIAL_CHARACTER + STR_UMLAUT),
		random_string(length=1, alpha=False, numeric=False, charset=STR_UMLAUTNUM)
	))


random_username = random_name
random_groupname = random_name


def random_int(bottom_end=0, top_end=9):
	# type: (int, int) -> str
	return str(randint(bottom_end, top_end))


def random_version(elements=3):
	# type: (int) -> str
	return '.'.join(random_int(0, 9) for _ in range(elements))


def random_ucs_version(min_major=1, max_major=9, min_minor=0, max_minor=99, min_patchlevel=0, max_patchlevel=99):
	# type: (int, int, int, int, int, int) -> str
	return '%s.%s-%s' % (
		randint(min_major, max_major),
		randint(min_minor, max_minor),
		randint(min_patchlevel, max_patchlevel),
	)


def random_mac():
	# type: () -> str
	return ':'.join(
		"%02x" % (randint(0, 0x7f if i < 4 else 0xff),)
		for i in range(6)
	)


def random_ip(ip_iter=iter(range(11, 121))):
	# type: (Iterator[int]) -> str
	"""Returns 110 different ip addresses in the range 11.x.x.x-120.x.x.x"""
	return '%d.%d.%d.%d' % (
		next(ip_iter),
		randint(1, 254),
		randint(1, 254),
		randint(1, 254),
	)


def random_subnet(ip_iter=iter(range(11, 121))):
	# type: (Iterator[int]) -> str
	"""Returns 110 different ip addresses in the range 11.x.x.x-120.x.x.x"""
	return '%d.%d.%d' % (
		next(ip_iter),
		randint(1, 254),
		randint(1, 254),
	)


def random_ipv6_subnet():
	# type: () -> str
	"""Returns random six blocks of an ipv6 address """
	m = 16**4
	return ":".join(("%04x" % randint(0, m) for i in range(6)))


def random_domain_name(length=10):
	# type: (int) -> str
	return '%s.%s' % (
		random_string(length=length // 2, alpha=True, numeric=False),
		random_string(length=length - length // 2, alpha=True, numeric=False),
	)


def random_dns_record():
	# type: () -> str
	# Bug #49679: the S4-Connector always appends a dot to nSRecord and ptrRecords without dot
	return '%s.' % (random_string(),)


def random_date():  # type: () -> str
	return '20%02d-%02d-%02d' % (randint(0, 99), randint(1, 12), randint(1, 27))


def random_time(range_hour=(0, 23)):  # type: (Optional[Tuple[int]]) -> str
	return '%02d:%02d:%02d' % (randint(*range_hour), randint(0, 60), randint(0, 60))


def random_email():  # type: () -> str
	return '%s@%s' % (random_name(), random_domain_name())
