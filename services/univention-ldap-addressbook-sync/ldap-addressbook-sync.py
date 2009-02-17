#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention LDAP addressbook synchronisation
#
#
# Copyright (C) 2008, 2009 Univention GmbH
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

import listener, cPickle, time, os, subprocess
import univention.debug

name = 'ldap-addressbook-sync'
description = 'synchronize LDAP addressbook to IMAP shared folder'
filter = '(|(objectClass=inetOrgPerson)(objectClass=univentionGroup)(objectClass=univentionKolabGroup))'
attributes = []
datadir = listener.baseConfig.get('ldap/addressbook/sync/dir', '/var/lib/univention-ldap-addressbook-sync')

def __add_cache_entry( dn, new, old ):

	listener.setuid( 0 )

	if not os.path.exists( datadir ):
		univention.debug.debug( univention.debug.LISTENER, univention.debug.WARN,
								'LDAP ADDRESSBOOK SYNC: creating %s' % datadir )
		os.mkdir(datadir)
	try:
		obj = ( dn, new, old )

		fn = os.path.join( datadir, "%f" % time.time() )
		univention.debug.debug( univention.debug.LISTENER, univention.debug.INFO,
								'LDAP ADDRESSBOOK SYNC: writing %s' % fn )
		fd = open( fn, 'w+' )
		os.chmod( fn, 0600 )
		cPickle.dump( obj, fd )
		fd.close()
	finally:
		listener.unsetuid()

def __check_relevance( obj, dn, new, old ):
	obj_classes = obj.get( 'objectClass', [] )
	# mail address available ?
	univention.debug.debug( univention.debug.LISTENER, univention.debug.INFO, str( obj ) )
	if ( 'univentionGroup' in obj_classes or 'univentionKolabGroup' in obj_classes ) and \
		   obj.get( 'mailPrimaryAddress', None ):
		__add_cache_entry( dn, new, old )
		return True
	elif 'inetOrgPerson' in obj_classes:
		__add_cache_entry( dn, new, old )
		return True

	return False

def handler( dn, new, old ):
	univention.debug.debug( univention.debug.LISTENER, univention.debug.INFO, 'handler' )
	# added object
	if not old and new:
		univention.debug.debug( univention.debug.LISTENER, univention.debug.INFO, 'LDAP ADDRESSBOOK SYNC: add' )
		__check_relevance( new, dn, new, old )
	# removed object
	elif old and not new:
		univention.debug.debug( univention.debug.LISTENER, univention.debug.INFO, 'LDAP ADDRESSBOOK SYNC: remove' )
		__check_relevance( old, dn, new, old )
	# modified object
	else:
		univention.debug.debug( univention.debug.LISTENER, univention.debug.INFO, 'LDAP ADDRESSBOOK SYNC: modify' )
		__check_relevance( old, dn, new, old )
		if not __check_relevance( new, dn, new, old ):
			__check_relevance( old, dn, new, old )

def clean():
	univention.debug.debug( univention.debug.LISTENER, univention.debug.INFO, 'LDAP ADDRESSBOOK SYNC: reset addressbook folder (clean)' )
	listener.setuid(0)
	subprocess.call( [ '/usr/sbin/univention-ldap-addressbook-sync', '--remove-all-contacts' ] )
	try:
		for filename in os.listdir(datadir):
			os.remove(os.path.join(datadir, filename))
	finally:
		listener.unsetuid()


def postrun():
	univention.debug.debug( univention.debug.LISTENER, univention.debug.INFO, 'LDAP ADDRESSBOOK SYNC: calling univention-ldap-addressbook-sync' )
	listener.setuid( 0 )
	try:
		listener.run( '/usr/sbin/univention-ldap-addressbook-sync', ['univention-ldap-addressbook-sync' ], uid = 0, wait = None )
	finally:
		listener.unsetuid()
	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'LDAP ADDRESSBOOK SYNC: univention-ldap-addressbook-sync finished')


def initialize():
	clean()
