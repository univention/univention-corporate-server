# -*- coding: utf-8 -*-
#
# Univention Package Database
#  listener module
#
# Copyright 2004-2022 Univention GmbH
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

from __future__ import absolute_import

import os
from listener import configRegistry, SetUID
import subprocess
import univention.debug as ud

name = 'pkgdb'
description = 'Package-Database'
filter = '(|(objectClass=univentionDomainController)(objectClass=univentionClient)(objectClass=univentionMemberServer))'
attributes = ['uid']

ADD_DIR = '/var/lib/univention-pkgdb/add'
DELETE_DIR = '/var/lib/univention-pkgdb/delete'


def exec_pkgdb(args):
	# type: (list) -> int
	ud.debug(ud.LISTENER, ud.INFO, "exec_pkgdb args=%s" % args)

	with SetUID(0):
		cmd = ['univention-pkgdb-scan', '--db-server=%(hostname)s.%(domainname)s' % configRegistry]
		cmd += args
		retcode = subprocess.call(cmd)

	ud.debug(ud.LISTENER, ud.INFO, "pkgdb: return code %d" % retcode)
	return retcode


def add_system(sysname):
	# type: (str) -> int
	retcode = exec_pkgdb(['--add-system', sysname])
	if retcode != 0:
		ud.debug(ud.LISTENER, ud.ERROR, "error while adding system=%s to pkgdb" % sysname)
	else:
		ud.debug(ud.LISTENER, ud.INFO, "successful added system=%s" % sysname)
	return retcode


def del_system(sysname):
	# type: (str) -> int
	retcode = exec_pkgdb(['--del-system', sysname])
	if retcode != 0:
		ud.debug(ud.LISTENER, ud.ERROR, "error while deleting system=%s to pkgdb" % sysname)
	else:
		ud.debug(ud.LISTENER, ud.INFO, "successful added system=%s" % sysname)
	return retcode


def initialize():
	# TODO: call add_system for every system in the directory already
	pass


def handler(dn, new, old):
	# type: (str, dict, dict) -> None
	ud.debug(ud.LISTENER, ud.INFO, "pkgdb handler dn=%s" % (dn))

	with SetUID(0):
		if old and not new:
			if 'uid' in old:
				uid = old['uid'][0].decode('UTF-8')
				if del_system(uid) != 0:
					with open(os.path.join(DELETE_DIR, uid), 'w') as fd:
						fd.write(uid + '\n')

		elif new and not old:
			if 'uid' in new:
				uid = new['uid'][0].decode('UTF-8')
				if add_system(uid) != 0:
					with open(os.path.join(ADD_DIR, uid), 'w') as fd:
						fd.write(uid + '\n')
