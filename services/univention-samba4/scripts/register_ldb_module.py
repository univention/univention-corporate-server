#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Samba
#  listener module: manage idmap
#
# Copyright 2001-2019 Univention GmbH
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

import optparse
import sys
from samba.param import LoadParm
from samba.auth import system_session
from samba import Ldb
import ldb

if __name__ == "__main__":

	parser = optparse.OptionParser("%prog [options]")
	parser.add_option("-v", "--verbose", action="store_true", dest="verbose")
	parser.add_option("-H", dest="ldburl", help="LDB Url")
	parser.add_option("--prepend", dest="prepend", action="append", help="Prepend LDB module", default=[])
	parser.add_option("--append", dest="append", action="append", help="Append LDB module", default=[])
	parser.add_option("--remove", dest="remove", action="append", help="Append LDB module", default=[])
	parser.add_option("--check", dest="check", action="store_true", help="Check registered LDB modules", default=[])
	parser.add_option("--ignore-exists", dest="ignore_exists", action="store_true", help="Don't add LDB modules already registered")
	parser.add_option("--dry-run", dest="dry_run", action="store_true", help="Dry run")
	opts, args = parser.parse_args()

	if not (opts.prepend or opts.append or opts.remove or opts.check):
		parser.print_help()
		sys.exit(1)

	lp = LoadParm()
	lp.load('/etc/samba/smb.conf')

	ldb_object = Ldb(opts.ldburl, lp=lp, session_info=system_session())
	msg = ldb_object.search(base="@MODULES", scope=ldb.SCOPE_BASE, attrs=['@LIST'])

	assert len(msg) == 1
	assert "@LIST" in msg[0]

	if opts.verbose:
		print "Current @LIST:", msg[0]["@LIST"]
	if opts.check and not opts.dry_run:
		sys.exit(0)

	if len(msg[0]["@LIST"]) == 1:
		modules_0 = msg[0]["@LIST"][0]
		modules_list_0 = modules_0.split(',')

		if opts.remove:
			# LDB Modules are organised as a stack, remove the last occurrence
			modules_list_0.reverse()
			for module in opts.remove:
				try:
					modules_list_0.remove(module)
				except ValueError:
					print "Module %s not in @LIST, ignoring" % module
			modules_list_0.reverse()

		updated_modules = []
		for module in opts.prepend:
			if opts.ignore_exists and module in modules_list_0:
				continue
			else:
				updated_modules.append(module)
		updated_modules.extend(modules_list_0)
		for module in opts.append:
			if opts.ignore_exists and module in modules_list_0:
				continue
			else:
				updated_modules.append(module)
		updated_modules_str = ','.join(updated_modules)

		if opts.dry_run:
			print "Dry run @LIST:", updated_modules_str
			sys.exit(0)

		modify_msg = ldb.Message()
		modify_msg.dn = ldb.Dn(ldb_object, "@MODULES")
		modify_msg["@LIST"] = ldb.MessageElement([updated_modules_str], ldb.FLAG_MOD_REPLACE, "@LIST")
		ldb_object.modify(modify_msg)
		if opts.verbose:
			msg = ldb_object.search(base="@MODULES", scope=ldb.SCOPE_BASE, attrs=['@LIST'])
			print "Updated @LIST:", msg[0]["@LIST"]
	else:
		print "Current @LIST attribute is multivalued, can't handle this"
		sys.exit(1)
