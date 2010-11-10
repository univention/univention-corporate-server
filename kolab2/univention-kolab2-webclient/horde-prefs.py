# -*- coding: utf-8 -*-
#
# Univention Kolab2 Webclient
#  set default perferences for a horde user
#
# Copyright 2004-2010 Univention GmbH
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

name='horde-prefs'
description='set a default identity in the horde preferences database'
filter='(objectClass=kolabInetOrgPerson)'
attributes=[]

import listener, univention_baseconfig
import univention.debug

import pg, string


def __create_db_identity( mail, fullname, from_addr ):
 	name = 'Default Identity'
	return 'a:1:{i:0;a:4:{s:2:\"id\";s:%d:\"%s\";s:8:\"fullname\";s:%d:\"%s\";s:9:\"from_addr\";s:%d:\"%s\";s:16:\"default_identity\";s:1:\"1\";}}' % \
			( len( name ), name, len( fullname ), fullname, len( from_addr ), from_addr )

def __tuples_exist ( db, mail, scope ):
	return 0 < db.query( "select * from horde_prefs where pref_uid='%s' and pref_scope='%s';" % (mail, scope) ).ntuples()

def __imp_settings ( db, mail ):
	if not __tuples_exist ( db, mail, 'imp' ):
		db.query( "insert into horde_prefs values('%s', 'imp', 'search_sources', '%s\tkolab_global');" % (mail, mail))
		db.query( "insert into horde_prefs values('%s', 'imp', 'search_fields', '%s\tfirstname\tlastname\temails\r\nkolab_global\tname\tfirstname\tlastname\temail');" % (mail, mail))

def __triple_exist ( db, mail, scope, name ):
	return 0 < db.query( "select * from horde_prefs where pref_uid='%s' and pref_scope='%s' and pref_name='%s';" % (mail, scope, name) ).ntuples()

def __quadruple_exist ( db, mail, scope, name, value ):
	return 0 < db.query( "select * from horde_prefs where pref_uid='%s' and pref_scope='%s' and pref_name='%s' and pref_value='%s';" % (mail, scope, name, value) ).ntuples()

def __turba_settings ( db, mail ):
	if not __tuples_exist ( db, mail, 'turba' ):
		db.query( "insert into horde_prefs values('%s', 'turba', 'default_dir', '%s');" % (mail, mail))
		db.query( "insert into horde_prefs values('%s', 'turba', 'addressbooks', '%s\nkolab_global');" % (mail, mail))

def __kronolith_settings ( db, mail ):
	if not __tuples_exist ( db, mail, 'kronolith' ):
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
		db.query( "insert into horde_prefs values('%s', 'kronolith', 'default_share', '%s');" % (mail, mail))
		db.query( "insert into horde_prefs values('%s', 'kronolith', 'fb_cals', 'a:1:{i:0;s:%d:\"%s\";}');" % (mail, len(mail), mail))
		db.query( "insert into horde_prefs values('%s', 'kronolith', 'display_cals', 'a:1:{i:0;s:%d:\"%s\";}');" % (mail, len(mail), mail))

def __horde_settings ( db, mail, fullname, from_addr ):
	if not __tuples_exist ( db, mail, 'horde' ):
		baseConfig = univention_baseconfig.baseConfig()
		baseConfig.load()

		menu_width = baseConfig.get('horde/menu/width', '200')
		categories = {}
		for k in baseConfig.keys():
			if k.startswith('horde/calendar/category/'):
				categories[k.split('/')[-1]] = '#%s' % baseConfig[k]

		db.query( "insert into horde_prefs values('%s','horde', 'identities','%s');" % (mail, __create_db_identity( mail, fullname, from_addr )) )
		db.query( "insert into horde_prefs values('%s', 'horde', 'confirm_maintenance', '0');" % mail )
		db.query( "insert into horde_prefs values('%s', 'horde', 'do_maintenance', '0');" % mail )
		db.query( "insert into horde_prefs values('%s', 'horde', 'show_last_login', '1');" % mail )
		db.query( "insert into horde_prefs values('%s', 'horde', 'widget_accesskey', '1');" % mail )
		db.query( "insert into horde_prefs values('%s', 'horde', 'initial_application', 'horde');" % mail )
		db.query( "insert into horde_prefs values('%s', 'horde', 'menu_refresh_time', '300');" % mail )
		db.query( "insert into horde_prefs values('%s', 'horde', 'menu_view', 'both');" % mail )
		db.query( "insert into horde_prefs values('%s', 'horde', 'sidebar_width', '%s');" % (mail, menu_width ))
		db.query( "insert into horde_prefs values('%s', 'horde', 'show_sidebar', '1');" % mail )
		db.query( "insert into horde_prefs values('%s', 'horde', 'summary_refresh_time', '300');" % mail )
		db.query( "insert into horde_prefs values('%s', 'horde', 'theme', 'silver');" % mail )
		db.query( "insert into horde_prefs values('%s', 'horde', 'date_format', '%%A, %%d. %%B %%Y');" % mail )
		db.query( "insert into horde_prefs values('%s', 'horde', 'twentyFour', '1');" % mail )
		db.query( "insert into horde_prefs values('%s', 'horde', 'timezone', '0');" % mail )
		db.query( "insert into horde_prefs values('%s', 'horde', 'language', '0');" % mail )
		db.query( "insert into horde_prefs values('%s', 'horde', 'add_source', '%s');" % (mail, mail) )

		if len(categories) > 0:
			db.query( "insert into horde_prefs values('%s', 'horde', 'categories', '%s');" % (mail,string.join(categories.keys(),'|') ) )
			category_colors = '_default_:#FFFFFF|_unfiled_:#DDDDDD'
			for k in categories.keys():
				category_colors = '%s:%s|%s' % (k, categories[k],category_colors)
			db.query( "insert into horde_prefs values('%s', 'horde', 'category_colors', '%s');" % (mail,category_colors))
			#category_colors          | bla:#FFFFFF|foobar:#112233|_default_:#FFFFFF|_unfiled_:#DDDDDD
	elif __triple_exist(db, mail, 'horde', 'identities') and not __quadruple_exist(db, mail, 'horde', 'identities', __create_db_identity( mail, fullname, from_addr )):
		db.query( "update horde_prefs set pref_value='%s' where pref_uid='%s' and pref_scope='%s' and pref_name='%s';" % (__create_db_identity( mail, fullname, from_addr ), mail, 'horde', 'identities'))

def handler(dn, new, old):
	if new and new.has_key( 'mailPrimaryAddress' ):
		listener.setuid(0)
		try:
			secret = open( '/etc/horde.secret', 'r' )
			password = secret.readlines()[ 0 ][ : -1 ]
			secret.close()
			db = pg.connect( dbname = 'horde', user = 'horde', passwd = password )
			try:
				from_attr=listener.baseConfig.get('horde/identities/from_attr', 'mailPrimaryAddress')
				from_addr_list=new.get(from_attr)
				if from_addr_list:
					from_addr=from_addr_list[0]
				else:
					univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, '%s: Attribute "%s" is not set for user with mailPrimaryAddress %s' % (__file__, from_attr, new['mailPrimaryAddress'][0]))
					from_addr=''

				__horde_settings( db, mail = new['mailPrimaryAddress'][0], fullname = new[ 'displayName' ][0], from_addr=from_addr )
				__kronolith_settings( db, mail = new['mailPrimaryAddress'][0] )
				__turba_settings( db, mail = new['mailPrimaryAddress'][0] )
				__imp_settings( db, mail = new['mailPrimaryAddress'][0] )
			finally:
				db.close()
		finally:
			listener.unsetuid()

