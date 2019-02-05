#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Directory Listener
"""Resync objects from master to local LDAP database"""
#
# Copyright 2004-2019 Univention GmbH
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

from __future__ import print_function
import univention.uldap as uldap
import univention.config_registry

import ldap
import ldap.modlist
import optparse


def main():
	usage = "usage: %prog [options]"
	parser = optparse.OptionParser(usage=usage, description=__doc__)
	parser.add_option("-f", "--filter", help="resync objects from master found by this filter")
	parser.add_option("-r", "--remove", action="store_true", help="remove objects in local database before resync")
	parser.add_option("-s", "--simulate", action="store_true", help="dry run, do not remove or add")
	opts, args = parser.parse_args()

	ucr = univention.config_registry.ConfigRegistry()
	ucr.load()
	base = ucr.get("ldap/base")
	binddn = "cn=update,%s" % base
	with open("/etc/ldap/rootpw.conf", "r") as fh:
		for line in fh:
			line = line.strip()
			if line.startswith('rootpw '):
				bindpw = line[7:].strip('"')
				break
		else:
			exit(1)

	if not opts.filter:
		opts.filter = '(uid=%s$)' % ucr['hostname']

	# get local and master connection
	local = uldap.access(binddn=binddn, bindpw=bindpw, start_tls=0, host="localhost", port=389)
	if ucr.get("server/role", "") == "domaincontroller_backup":
		master = uldap.getAdminConnection()
	else:
		master = uldap.getMachineConnection(ldap_master=True)

	# delete local
	if opts.remove:
		res = local.search(base=base, filter=opts.filter)
		for dn, data in res:
			print("remove from local: %s" % (dn,))
			if not opts.simulate:
				local.delete(dn)

	# resync from master
	res = master.search(base=base, filter=opts.filter)
	for dn, data in res:
		print("resync from master: %s" % (dn,))
		if not opts.simulate:
			local.add(dn, ldap.modlist.addModlist(data))


if __name__ == "__main__":
	main()
