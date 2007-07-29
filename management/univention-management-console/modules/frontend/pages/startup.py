#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  base class for UMC module pages
#
# Copyright (C) 2006, 2007 Univention GmbH
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
import univention.management.console.dialog as umcd
import univention.management.console.tools as umc_tools

from urllib import quote, urlencode
from urlparse import urlunparse

_ = umc.Translation( 'univention.management.console.frontend' ).translate

class Command( object ):
	MAIL_ADDRESS = quote( 'Univention Feedback <feedback@univention.de>' )
	MAIL_SUBJECT = _( 'Bugreport: Univention Management Console' )
	MAIL_TEXT = _( '''
Please take a second to provide the following information

1) Steps to reproduce the failure

2) Expected result

3) Actual result

''' )

	def __init__( self, request, name, description, priority, caching ):
		self.request = request
		self.priority = priority
		self.name = name
		self.description = description
		self.caching = caching
		self.cache = None
		self.referrer = None
		self.__error_dialog = None

	def __mail_report_link( self, report ):
		body = Command.MAIL_TEXT + report
		url = urlunparse( ( 'mailto', '', Command.MAIL_ADDRESS, '',
							urlencode( { 'subject' : unicode( Command.MAIL_SUBJECT ),
										 'body' : unicode( body ) } ), '' ) )
		return url.replace( '+', '%20' )

	def error_message( self, report = None, exception = False ):
		rows = []
		if report:
			lst = umcd.List()
			if exception:
				lst.add_row( [ umcd.Image( 'actions/critical', umc_tools.SIZE_MEDIUM ),
							   umcd.HTML( '<pre>%s</pre>' % report ) ] )
				text = _( 'Report this error to Univention Feedback &lt;feedback@univention.de&gt;' )
				lst.add_row( [ '', umcd.Link( text, self.__mail_report_link( report ) ) ] )
			else:
				lst.add_row( [ umcd.Image( 'actions/critical', umc_tools.SIZE_MEDIUM ), report ] )
			lst.add_row( [ '', umcd.ErrorButton() ] )
			frame = umcd.Frame( [ lst ], _( 'An Error has occured' ) )
			self.__error_dialog = umcd.Dialog( [ frame ] )

		return self.__error_dialog

	def error_active( self ):
		return self.__error_dialog != None

	def error_reset( self ):
		del self.__error_dialog
		self.__error_dialog = None

	def is_startup( self ):
		return self.request.incomplete

	def use_referrer( self ):
		return not self.request.has_flag( 'web:startup_referrer' ) or \
			   self.request.get_flag( 'web:startup_referrer' )

	def reload( self ):
		return self.request.has_flag( 'web:startup_reload' ) and \
			   self.request.get_flag( 'web:startup_reload' )

	def dialog( self ):
		return self.request.has_flag( 'web:startup_dialog' ) and \
			   self.request.get_flag( 'web:startup_dialog' )

class List( list ):
	def __init__( self ):
		list.__init__( self )

	def add( self, request, name, description, priority = 0, caching = False ):
		newcmd = Command( request, name, description, priority, caching )
		if not priority:
			self.append( newcmd )
			return len( self ) - 1

		i = 0
		for cmd in self:
			if newcmd.priority > cmd.priority:
				self.insert( i, newcmd )
				return i
			i += 1
		else:
			self.append( newcmd )
			return len( self ) - 1

	def remove( self, i ):
		if i < len( self ):
			list.__delitem__( self, i )

	def categories( self ):
		return map( lambda cmd: ( cmd.name, cmd.description, cmd.is_startup() ), self )

	def __getitem__( self, i ):
		if i < len( self ):
			return list.__getitem__( self, i )
		return None

	def find( self, request ):
		i = 0
		for cmd in self:
			if cmd.request.arguments[ 0 ] == request.arguments[ 0 ]:
				if cmd.request.incomplete and request.incomplete:
					return i
				if cmd.request.incomplete == request.incomplete and \
					   cmd.request.options == request.options:
					return i
			i += 1

		return -1
