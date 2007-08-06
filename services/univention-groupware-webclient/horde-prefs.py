#
# Univention Groupware Webclient
#  set default perferences for a horde user
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

name='horde-prefs'
description='set a default identity in the horde preferences database'
filter='(objectClass=kolabInetOrgPerson)'
attributes=[]

import listener, univention_baseconfig
import univention.debug

import pg

baseConfig = univention_baseconfig.baseConfig()

def __create_db_identity( mail, fullname ):
 	name = 'Default Identity'
	return 'a:1:{i:0;a:4:{s:2:\"id\";s:%d:\"%s\";s:8:\"fullname\";s:%d:\"%s\";s:9:\"from_addr\";s:%d:\"%s\";s:16:\"default_identity\";s:1:\"1\";}}' % \
			( len( name ), name, len( fullname ), fullname, len( mail ), mail )

def handler(dn, new, old):
	if not old and new and new.has_key( 'mailPrimaryAddress' ):
		listener.setuid(0)
		try:
			secret = open( '/etc/horde.secret', 'r' )
			password = secret.readlines()[ 0 ][ : -1 ]
			secret.close()
			db = pg.connect( dbname = 'horde', user = 'horde', passwd = password )
			sql_cmd = "insert into horde_prefs values('%s','horde', 'identities','%s');" % (new[ 'mailPrimaryAddress' ][0], __create_db_identity( mail = new[ 'mailPrimaryAddress' ][0], fullname = new[ 'displayName' ][0] ))
			univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'SQL cmd=%s' % sql_cmd)
			db.query( sql_cmd )
			db.close( )
		finally:
			listener.unsetuid()

