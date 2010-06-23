#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  base class for UMC module pages
#
# Copyright 2006-2010 Univention GmbH
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

import univention.management.console as umc
import univention.management.console.dialog as umcd
import univention.management.console.tools as umc_tools

from urllib import quote, urlencode
from urlparse import urlunparse

import univention.config_registry
import v

_ = umc.Translation( 'univention.management.console.frontend' ).translate

class Command( object ):
	ucr = univention.config_registry.ConfigRegistry()
	ucr.load()
	MAIL_ADDRESS_EMAIL =  ucr.get('umc/web/feedback/mail', 'feedback@univention.de')
	MAIL_ADDRESS_DESCRIPTION = ucr.get('umc/web/feedback/description', 'Univention Feedback')
	MAIL_ADDRESS = quote('%s <%s>' % (MAIL_ADDRESS_DESCRIPTION, MAIL_ADDRESS_EMAIL))
	MAIL_SUBJECT = _( 'Bugreport: Univention Management Console Traceback' )
	MAIL_TEXT = _( '''
Please take a second to provide the following information

1) Steps to reproduce the failure

2) Expected result

3) Actual result

----------

''' )
	VERSION = '''
----------

Univention Management Console Version: %s - %s
''' % (v.version, v.build)


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
		body = Command.MAIL_TEXT + report + Command.VERSION
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
				text = _( 'Report this error to %s &lt;%s&gt;' % (Command.MAIL_ADDRESS_DESCRIPTION, Command.MAIL_ADDRESS_EMAIL) )
				lst.add_row( [ '', umcd.Link( text, self.__mail_report_link( report ) ) ] )
			else:
				lst.add_row( [ umcd.Image( 'actions/critical', umc_tools.SIZE_MEDIUM ), report ] )
			lst.add_row( [ '', umcd.ErrorButton() ] )
			frame = umcd.Frame( [ lst ], _( 'An error has occured' ) )
			self.__error_dialog = umcd.Dialog( [ frame ] )

		return self.__error_dialog

	def info_message( self, report ):
		rows = []
		lst = umcd.List()
		lst.add_row( [ umcd.Image( 'actions/info', umc_tools.SIZE_MEDIUM ), str( report ) ] )
		lst.add_row( [ '', umcd.ErrorButton() ] )
		frame = umcd.Frame( [ lst ], _( 'Information' ) )

		return umcd.Dialog( [ frame ] )

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
