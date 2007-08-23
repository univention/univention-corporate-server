# -*- coding: utf-8 -*-
#
# Univention Groupware Webclient
#  set default perferences for a horde user
#
# Copyright (C) 2004, 2005, 2006, 2007 Univention GmbH
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


def __kronolith_settings ( db, mail ):
	db.query( "insert into horde_prefs values('%s', 'kronolith', 'show_shared_side_by_side', '0');" % mail)
	db.query( "insert into horde_prefs values('%s', 'kronolith', 'show_fb_legend', '1');" % mail)
	db.query( "insert into horde_prefs values('%s', 'kronolith', 'show_panel', '1');" % mail)
	db.query( "insert into horde_prefs values('%s', 'kronolith', 'show_legend', '1');" % mail)
	db.query( "insert into horde_prefs values('%s', 'kronolith', 'show_icons', '1');" % mail)
	db.query( "insert into horde_prefs values('%s', 'kronolith', 'slots_per_hour', '1');" % mail)
	db.query( "insert into horde_prefs values('%s', 'kronolith', 'day_hour_force', '0');" % mail)
	db.query( "insert into horde_prefs values('%s', 'kronolith', 'day_hour_end', '44');" % mail)
	db.query( "insert into horde_prefs values('%s', 'kronolith', 'day_hour_start', '16');" % mail)
	db.query( "insert into horde_prefs values('%s', 'kronolith', 'week_start_monday', '1');" % mail)
	db.query( "insert into horde_prefs values('%s', 'kronolith', 'time_between_days', '0');" % mail)
	db.query( "insert into horde_prefs values('%s', 'kronolith', 'defaultview', 'week');" % mail)
	db.query( "insert into horde_prefs values('%s', 'kronolith', 'confirm_delete', '1');" % mail)

def __horde_settings ( db, mail, fullname ):
	db.query( "insert into horde_prefs values('%s','horde', 'identities','%s');" % (mail, __create_db_identity( mail, fullname )) )
	db.query( "insert into horde_prefs values('%s', 'horde', 'confirm_maintenance', '0');" % mail )
	db.query( "insert into horde_prefs values('%s', 'horde', 'do_maintenance', '0');" % mail )
	db.query( "insert into horde_prefs values('%s', 'horde', 'show_last_login', '1');" % mail )
	db.query( "insert into horde_prefs values('%s', 'horde', 'widget_accesskey', '1');" % mail )
	db.query( "insert into horde_prefs values('%s', 'horde', 'initial_application', 'horde');" % mail )
	db.query( "insert into horde_prefs values('%s', 'horde', 'menu_refresh_time', '300');" % mail )
	db.query( "insert into horde_prefs values('%s', 'horde', 'menu_view', 'both');" % mail )
	db.query( "insert into horde_prefs values('%s', 'horde', 'sidebar_width', '200');" % mail )
	db.query( "insert into horde_prefs values('%s', 'horde', 'show_sidebar', '1');" % mail )
	db.query( "insert into horde_prefs values('%s', 'horde', 'summary_refresh_time', '300');" % mail )
	db.query( "insert into horde_prefs values('%s', 'horde', 'theme', 'univention');" % mail )
	db.query( "insert into horde_prefs values('%s', 'horde', 'date_format', '%%A, %%d. %%B %%Y');" % mail )
	db.query( "insert into horde_prefs values('%s', 'horde', 'twentyFour', '1');" % mail )
	db.query( "insert into horde_prefs values('%s', 'horde', 'timezone', '0');" % mail )
	db.query( "insert into horde_prefs values('%s', 'horde', 'language', '0');" % mail )

def handler(dn, new, old):
	if not old and new and new.has_key( 'mailPrimaryAddress' ):
		listener.setuid(0)
		try:
			secret = open( '/etc/horde.secret', 'r' )
			password = secret.readlines()[ 0 ][ : -1 ]
			secret.close()
			db = pg.connect( dbname = 'horde', user = 'horde', passwd = password )

			__horde_settings( db, mail = new[ 'mailPrimaryAddress' ][0], fullname = new[ 'displayName' ][0] )
			__kronolith_settings( db, mail = new[ 'mailPrimaryAddress' ][0] )

			db.close( )
		finally:
			listener.unsetuid()

