#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMCP proxy implementation: redirects requests to a specified list of
#  hosts, collects the responses and returns a result create by merging
#  the retrieved responses.
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

# internal packages
import server
import session
import message

import univention.debug as ud

__all__ = [ 'Proxy' ]

class ProxySession( object ):
	'''Such an object describes a connection to client plus several
	connections to the UMC servers that process the request'''
	def __init__( self ):
		self.clients


class ProxyProcessor( session.Processor ):
	def __init__( self, username, password ):
		session.Processor.__init__( self, username, password )
		self.__sessions = []

	def request( self, msg ):
		'''This method is invoked wenn the server has received an
		incoming UMCP request after a successfull athentication. The
		default server starts the local processing of the request, but
		this proxy processor redirects the request to the specified
		hosts, if the user is allowed to'''
		hosts = []

		# everything but a COMMAND request can be handled by the default
		# processor
		if msg.command != 'COMMAND':
			session.Processor.request( self, msg )

		# check existence and permissions for the requested command
		if self.__is_command_known( msg ):
			if msg.hosts:
				pass

class ProxyBucket( server.MagicBucket ):
	def __init__( self ):
		server.MagicBucket.__init__( self, processorClass = ProxyProcessor )

class Proxy( server.Server ):
	'''This class is mainly a UMCP server, with a slightly different
	configuration and another session handling (ProxyBucket)'''
	def __init__( self, port = 6671 ):
		server.Server.__init__( self, port, magicClass = ProxyBucket )
