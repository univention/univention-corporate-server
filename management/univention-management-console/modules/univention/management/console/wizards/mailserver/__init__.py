#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  wizard: mail server configuration
#
# Copyright (C) 2007-2009 Univention GmbH
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

_ = umc.Translation( 'univention.management.console.wizards.mailserver' ).translate

icon = 'wizards/mailserver/module'
short_description = _( 'Mail server' )
long_description = _( 'Mail server configuration' )
categories = [ 'wizards' ]

command_description = {
	'wizard/mailserver/show': umch.command(
		short_description = _( 'Mail server' ),
		long_description = _( 'View mail server configuration' ),
		method = 'mailserver_show',
		values = {},
		startup = True,
		priority = 100
	),
	'wizard/mailserver/set': umch.command(
		short_description = _( 'Mail server' ),
		long_description = _( 'Set mail server configuration' ),
		method = 'mailserver_set',
		values = { 'spam' : umc.Boolean( _( 'SPAM filtering' ) ),
				   'virus' : umc.Boolean( _( 'Virus filtering' ) ),
				   'imap' : umc.Boolean( _( 'IMAP access' ) ),
				   'imap_quota' : umc.Boolean( _( 'IMAP quota support' ) ),
				   'pop' : umc.Boolean( _( 'POP3 access' ) ),
				   'messagesizelimit' : umc.Integer( _( 'Maximum message size' ) ),
				   'root' : umc.EMailAddress( _( 'E-mail address alias for root' ) )
				   },
	),
}

def _get_bool( var, default ):
	if umc.baseconfig.has_key( var ):
		return umc.baseconfig.get( var ).lower() in ( 'yes', 'true', 'on', '1' )

	return default

def _2str( value ):
	if value:
		return 'yes'
	return 'no'

class handler( umch.simpleHandler, _revamp.Web ):
	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )
		_revamp.Web.__init__( self )

	def mailserver_show( self, object ):
		umc.baseconfig.load()
		self.finished( object.id(),
					   { 'spam' : _get_bool( 'mail/antispam', True ),
						 'virus' : _get_bool( 'mail/antivirus', True ),
						 'imap' : _get_bool( 'mail/cyrus/imap', True ),
						 'imap_quota' : _get_bool( 'mail/cyrus/imap/quota', True ),
						 'pop' : _get_bool( 'mail/cyrus/pop', True ),
						 'messagesizelimit' : umc.baseconfig.get( 'mail/messagesizelimit', 0 ),
						 'root' : umc.baseconfig.get( 'mail/alias/root', 0 ),
						 } )

	def _run_it( self, services, action ):
		failed = []
		for srv in services:
			if os.system( '/etc/init.d/%s %s' % ( srv, action ) ):
				failed.append( srv )
		return failed

	def mailserver_set( self, object ):
		ub.handler_set( [ 'mail/antispam=%s' % _2str( object.options[ 'spam' ] ) ] )
		ub.handler_set( [ 'mail/antivirus=%s' % _2str( object.options[ 'virus' ] ) ] )
		ub.handler_set( [ 'mail/cyrus/imap=%s' % _2str( object.options[ 'imap' ] ) ] )
		ub.handler_set( [ 'mail/cyrus/imap/quota=%s' % _2str( object.options[ 'imap_quota' ] ) ] )
		ub.handler_set( [ 'mail/cyrus/pop=%s' % _2str( object.options[ 'pop' ] ) ] )
		ub.handler_set( [ 'mail/messagesizelimit=%s' % object.options[ 'messagesizelimit' ] ] )
		ub.handler_set( [ 'mail/alias/root=%s' % object.options[ 'root' ] ] )
		cb = notifier.Callback( self._mailserver_set, object,
								_( 'Restarting the following services failed: %(services)s' ) )
		func = notifier.Callback( self._run_it, [ 'cyrus', 'postfix' ], 'restart' )
		thread = notifier.threads.Simple( 'mailserver', func, cb )
		thread.run()

		self.finished( object.id(), {} )


	def _mailserver_set( self, thread, result, object, error_messsage ):
		if result:
			self.finished( object.id(), {},
						   report = error_message % { 'services' : ', '.join( result ) },
						   success = False )
		else:
			self.finished( object.id(), {} )
