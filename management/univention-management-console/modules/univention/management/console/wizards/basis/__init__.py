#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  wizard: basis configuration
#
# Copyright (C) 2007 Univention GmbH
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

import univention.management.console as umc
import univention.management.console.protocol as umcp
import univention.management.console.handlers as umch
import univention.management.console.dialog as umcd
import univention.management.console.tools as umct

import univention.debug as ud
import univention_baseconfig as ub

import notifier
import notifier.popen

import os, re

import _revamp

_ = umc.Translation( 'univention.management.console.wizards.basis' ).translate

icon = 'wizards/basis/module'
short_description = _( 'Basis' )
long_description = _( 'Basis Configuration' )
categories = [ 'wizards' ]

command_description = {
	'wizard/basis/show': umch.command(
		short_description = _( 'Basis Configuration' ),
		long_description = _( 'View basis configuration' ),
		method = 'basis_show',
		values = {},
		startup = True,
		priority = 100
	),
	'wizard/basis/set': umch.command(
		short_description = _( 'Basis Configuration' ),
		long_description = _( 'Set basis configuration' ),
		method = 'basis_set',
		values = { 'hostname' : umc.String( _( 'Hostname' ) ),
				   'domainname' : umc.String( _( 'Domain Name' ) ),
				   'windows_domain' : umc.String( _( 'Windows Domain' ) ),
				   'ldap_base' : umc.String( _( 'LDAP Basis' ) ), },
	),
}

class handler( umch.simpleHandler, _revamp.Web ):
	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )
		_revamp.Web.__init__( self )

	def basis_show( self, object ):
		umc.baseconfig.load()
		self.finished( object.id(), { 'hostname' : umc.baseconfig.get( 'hostname', '' ),
									  'ldap_base' : umc.baseconfig.get( 'ldap/base', '' ),
									  'domainname' : umc.baseconfig.get( 'domainname', '' ),
									  'windows_domain' : umc.baseconfig.get( 'windows/domain', '' ), } )

	def basis_set( self, object ):
		umc.baseconfig.load()
		fp = open( '/var/cache/univention-system-setup/profile', 'w' )
		fp.write( "UMC_MODE=true\n" )
		for key, value in object.options.items():
			if value != umc.baseconfig.get( key.replace( '_', '/' ) ):
				fp.write( "%s=%s\n" % ( key.replace( '_', '/' ), value ) )
		fp.close()
		cb = notifier.Callback( self._basis_set, object )
		func = notifier.Callback( self._basis_run, object )
		thread = notifier.threads.Simple( 'basis', func, cb )
		thread.run()

	def _basis_run( self, object ):
		_path = '/usr/lib/univention-system-setup/scripts/basis/'
		failed = []
		for script in os.listdir( _path ):
			filename = os.path.join( _path, script )
			ud.debug( ud.ADMIN, ud.INFO, 'run script: %s' % filename )
			if os.path.isfile( filename ):
				if os.system( filename ):
					failed.append( script )
		return failed

	def _basis_set( self, thread, result, object ):
		if result:
			self.finished( object.id(), None,
						   report = _( 'The following scripts failed: %(scripts)s' ) % \
						   { 'scripts' : ', '.join( failed ) }, success = False )
		else:
			self.finished( object.id(), None )
