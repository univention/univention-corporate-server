# -*- coding: utf-8 -*-
#
# Univention Package Database
#  listener module
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import listener
import os,string
import univention.debug

name='pkgdb'
description='Package-Database'
filter='(|(objectClass=univentionDomainController)(objectClass=univentionClient)(objectClass=univentionMemberServer)(objectClass=univentionMobileClient))'
attributes=['uid']

hostname=listener.baseConfig['hostname']
domainname=listener.baseConfig['domainname']

ADD_DIR='/var/lib/univention-pkgdb/add'
DELETE_DIR='/var/lib/univention-pkgdb/delete'


def exec_pkgdb(args):
	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "exec_pkgdb args=%s" % args)

	listener.setuid(0)
	try:
		cmd = '/usr/lib/site-python/univention_pkgdb.py --db-server=%s.%s %s' % ( hostname, domainname, string.join( args, ' ' ))
		retcode = os.system( cmd )
	finally:
		listener.unsetuid()

	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "pkgdb: return code %d" % retcode)
	return retcode

def add_system( sysname ):
	retcode = exec_pkgdb(['--add-system', sysname])
	if retcode != 0:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, "error while adding system=%s to pkgdb" % sysname)
	else:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "successful added system=%s" % sysname)
	return retcode

def del_system( sysname ):
	retcode = exec_pkgdb(['--del-system', sysname])
	if retcode != 0:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, "error while deleting system=%s to pkgdb" % sysname)
	else:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "successful added system=%s" % sysname)
	return retcode

def initialize():
	pass

def handler(dn, new, old):
	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "pkgdb handler dn=%s" %(dn))


	try:
		if old and not new:
			if old.has_key('uid'):
				if del_system( old['uid'][0] ) != 0:
					listener.setuid(0)
					file = open( os.path.join(DELETE_DIR, old['uid'][0]), 'w' )
					file.write( old['uid'][0]  + '\n' )
					file.close()

		elif new and not old:
			if new.has_key('uid'):
				if (add_system( new['uid'][0] )) != 0:
					listener.setuid(0)
					file = open( os.path.join(ADD_DIR, new['uid'][0]), 'w' )
					file.write( new['uid'][0]  + '\n' )
					file.close()
	finally:
		listener.unsetuid()

def postrun():
	pass

def clean():
	pass
