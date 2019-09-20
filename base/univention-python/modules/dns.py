# -*- coding: utf-8 -*-
#
# Univention Python
#  DNS utilities
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

import DNS

DNS.DiscoverNameServers()


def lookup(query, type='a'):
	"""
	Lookup DNS entries of specified type.

	>>> lookup('localhost')
	['127.0.0.1']
	"""
	rr = DNS.DnsRequest(query, qtype=type).req().answers
	result = map(lambda x: x['data'], rr)
	return result


# for backward compatibility
from univention.ipv4 import *

if __name__ == '__main__':
	import doctest
	doctest.testmod()
