#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  Upgrade script for gPLink
#  Convert base64 objectGuid to S4 DN as used in s4cache.sqlite
#
# Copyright 2014-2019 Univention GmbH
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

import samba
import sys
import ldb
import base64
from optparse import OptionParser

from samba import dsdb
from samba.samdb import SamDB
from samba.param import LoadParm
from samba.auth import system_session
from samba.credentials import Credentials

if __name__ == '__main__':
	parser = OptionParser(usage='base64Guid2DN.py base64_guid')
	(options, args) = parser.parse_args()

	if len(args) != 1:
		parser.print_help()
		sys.exit(2)

	base64_guid = args[0]

	guid = base64.decodestring(base64_guid)

	lp = LoadParm()
	creds = Credentials()
	creds.guess(lp)
	samdb = SamDB(url='/var/lib/samba/private/sam.ldb', session_info=system_session(), credentials=creds, lp=lp)

	domain_dn = samdb.domain_dn()
	res = samdb.search(domain_dn, scope=ldb.SCOPE_SUBTREE, expression=("(objectGuid=%s)" % (guid)), attrs=["dn"])
	for msg in res:
		print msg.get("dn", idx=0)
