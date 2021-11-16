#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Directory Listener
#
# Copyright 2004-2021 Univention GmbH
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

"""Resync objects from Primary to local LDAP database"""

from __future__ import print_function

import argparse

import ldap
import ldap.modlist

import univention.config_registry
import univention.uldap as uldap


def main():
	# type: () -> None
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("-f", "--filter", help="resync objects from Primary found by this filter. Default: (uid=<hostname>$)")
	parser.add_argument("-r", "--remove", action="store_true", help="remove objects in local database before resync")
	parser.add_argument("-s", "--simulate", action="store_true", help="dry run, do not remove or add")
	parser.add_argument("-u", "--update", action="store_true", help="update/modify existing objects")
	opts = parser.parse_args()

	ucr = univention.config_registry.ConfigRegistry()
	ucr.load()
	base = ucr.get("ldap/base")
	server_role = ucr.get("server/role", "")
	if server_role == 'domaincontroller_master':
		print('local LDAP is Primary server, nothing to do')
		return
	if server_role not in ['domaincontroller_backup', 'domaincontroller_slave']:
		print('server role ("{}") has no LDAP, nothing to do'.format(server_role))
		return

	if not opts.filter:
		opts.filter = '(uid=%s$)' % ucr['hostname']

	# get local and Primary connection
	local = uldap.getRootDnConnection()
	if server_role == "domaincontroller_backup":
		master = uldap.getAdminConnection()
	else:
		master = uldap.getMachineConnection(ldap_master=True)

	# delete local
	if opts.remove:
		res = local.searchDn(base=base, filter=opts.filter)
		if not res:
			print('object does not exist local')
		for dn in res:
			print("remove from local: %s" % (dn,))
			if not opts.simulate:
				local.delete(dn)

	# resync from Primary
	res = master.search(base=base, filter=opts.filter)
	if not res:
		print('object does not exist on Primary')
	for dn, data in res:
		print("resync from Primary: %s" % (dn,))
		try:
			local_res = local.search(base=dn)
		except ldap.NO_SUCH_OBJECT:
			local_res = None
		if local_res and opts.remove and opts.simulate:
			local_res = None
		if not local_res and not opts.update:
			print('  ==> adding object')
			if not opts.simulate:
				local.add(dn, ldap.modlist.addModlist(data))
		elif not local_res and opts.update:
			print('  ==> object does not exist, can not update')
		elif local_res and opts.update:
			modlist = []
			local_data = local_res[0][1]
			for key in set(data.keys()) | set(local_data.keys()):
				if set(local_data.get(key, [])).symmetric_difference(set(data.get(key, []))):
					modlist.append([key, local_data.get(key, []), data.get(key, [])])
			if not modlist:
				print('  ==> no change')
			else:
				print('  ==> modifying object')
				if not opts.simulate:
					local.modify(dn, modlist)
		elif local_res and not opts.update:
			print('  ==> object does exist, can not create')


if __name__ == "__main__":
	main()
