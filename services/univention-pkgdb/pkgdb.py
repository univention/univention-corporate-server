# -*- coding: utf-8 -*-
#
# Univention Package Database
#  listener module
#
# Copyright 2004-2019 Univention GmbH
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
import listener
import subprocess
import univention.debug

name = 'pkgdb'
description = 'Package-Database'
filter = '(|(objectClass=univentionDomainController)(objectClass=univentionClient)(objectClass=univentionMemberServer)(objectClass=univentionMobileClient))'
attributes = ['uid']

hostname = listener.baseConfig['hostname']
domainname = listener.baseConfig['domainname']

ADD_DIR = '/var/lib/univention-pkgdb/add'
DELETE_DIR = '/var/lib/univention-pkgdb/delete'


def exec_pkgdb(args):
	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "exec_pkgdb args=%s" % args)

	listener.setuid(0)
	try:
		cmd = ['univention-pkgdb-scan', '--db-server=%s.%s' % (hostname, domainname, ), ]
		cmd += args
		retcode = subprocess.call(cmd)
	finally:
		listener.unsetuid()

	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "pkgdb: return code %d" % retcode)
	return retcode


def add_system(sysname):
	retcode = exec_pkgdb(['--add-system', sysname])
	if retcode != 0:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, "error while adding system=%s to pkgdb" % sysname)
	else:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "successful added system=%s" % sysname)
	return retcode


def del_system(sysname):
	retcode = exec_pkgdb(['--del-system', sysname])
	if retcode != 0:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, "error while deleting system=%s to pkgdb" % sysname)
	else:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "successful added system=%s" % sysname)
	return retcode


def initialize():
	# TODO: call add_system for every system in the directory already
	pass


def handler(dn, new, old):
	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "pkgdb handler dn=%s" % (dn))

	try:
		if old and not new:
			if 'uid' in old:
				if del_system(old['uid'][0]) != 0:
					listener.setuid(0)
					file = open(os.path.join(DELETE_DIR, old['uid'][0]), 'w')
					file.write(old['uid'][0] + '\n')
					file.close()

		elif new and not old:
			if 'uid' in new:
				if (add_system(new['uid'][0])) != 0:
					listener.setuid(0)
					file = open(os.path.join(ADD_DIR, new['uid'][0]), 'w')
					file.write(new['uid'][0] + '\n')
					file.close()
	finally:
		listener.unsetuid()


def postrun():
	pass


def clean():
	pass
