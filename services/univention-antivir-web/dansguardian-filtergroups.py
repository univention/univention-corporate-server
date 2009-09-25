# -*- coding: utf-8 -*-
#
# Univention Antivir Web
#  listener module: synchronize groups to UCR variables
#
# Copyright (C) 2009 Univention GmbH
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
import univention.config_registry as ucr
import univention.debug as ud

import subprocess

name='dansguardian-filtergroups'
description='Map user groups to UCR variables'
filter="(objectClass=univentionGroup)"
attributes=['memberUid']

keyPattern='dansguardian/groups/%s/members'

def initialize():
	pass

def handler( dn, new, old ):
	configRegistry = ucr.ConfigRegistry()
	configRegistry.load()
	hostdn = configRegistry[ 'ldap/hostdn' ]
	listener.setuid(0)
	try:
		changes = False
		# group has been removed
		if not new[ 'cn' ]:
			group = old[ 'cn' ][ 0 ]
			key = keyPattern % group.replace( ' ', '_' )
			if configRegistry.has_key( key ):
				ucr.handler_unset( [ key.encode() ] )
				changes = True
			return
		else:
			group = new[ 'cn' ][ 0 ]
			key = keyPattern % group.replace( ' ', '_' )

		# if this is not a dansguardian group
		ud.debug( ud.LISTENER, ud.ERROR, 'check group %s' % group )
		if not group in configRegistry.get( 'dansguardian/groups', 'www-access' ).split( ';' ):
			if configRegistry.has_key( keyPattern % group ):
				ucr.handler_unset( [ key.encode() ] )
				changes = True
			return

		if new and new.has_key( 'memberUid' ):
			keyval = '%s=%s' % ( key, ','.join( new[ 'memberUid' ] ) )
			ucr.handler_set( [ keyval.encode() ] )
			changes = True
	finally:
		listener.unsetuid()

	# reload dansguardian configuration
	if changes:
		subprocess.call( [ '/usr/sbin/dansguardian', '-g' ] )

def postrun():
	pass
