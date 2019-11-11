#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  Remove rejected UCS object
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

import os
import sqlite3
import sys
from optparse import OptionParser


class ObjectNotFound(BaseException):
	pass


def remove_ucs_rejected(ucs_dn):
	cache_db = sqlite3.connect('/etc/univention/connector/s4internal.sqlite')
	c = cache_db.cursor()
	c.execute("SELECT key FROM 'UCS rejected' WHERE value=?", [unicode(ucs_dn)])
	filenames = c.fetchall()
	if not filenames:
		raise ObjectNotFound
	for filename in filenames:
		if filename:
			if os.path.exists(filename[0]):
				os.remove(filename[0])
	c.execute("DELETE FROM 'UCS rejected' WHERE value=?", [unicode(ucs_dn)])
	cache_db.commit()
	cache_db.close()


if __name__ == '__main__':
	parser = OptionParser(usage='remove_ucs_rejected.py dn')
	(options, args) = parser.parse_args()

	if len(args) != 1:
		parser.print_help()
		sys.exit(2)

	ucs_dn = args[0]

	try:
		remove_ucs_rejected(ucs_dn)
	except ObjectNotFound:
		print 'ERROR: The object %s was not found.' % ucs_dn
		sys.exit(1)

	print 'The rejected UCS object %s has been removed.' % ucs_dn

	sys.exit(0)
