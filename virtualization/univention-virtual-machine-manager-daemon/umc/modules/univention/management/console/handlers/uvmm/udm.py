#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Virtual Machine Manager
#  module: UDM modules
#
# Copyright (C) 2010 Univention GmbH
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	 02110-1301	 USA

import univention.admin.uldap
import univention.admin.modules
import univention.admin.handlers.uvmm.profile as uvmm_profile

import univention.debug as ud

import univention.management.console as umc

_ = umc.Translation('univention.management.console.handlers.uvmm').translate

class ConnectionError( Exception ):
	pass

class Client( object ):
	PROFILE_RDN = 'cn=Profiles,cn=Virtual Machine Manager'

	def __init__( self ):
		self.co = None
		try:
			self.lo, self.position = univention.admin.uldap.getMachineConnection()
			self.base = "%s,%s" % ( Client.PROFILE_RDN, self.position.getDn() )
		except IOError, e:
			raise ConnectionError( _( 'Could not open LDAP connection' ) )

	def get_profiles( self ):
		try:
			res = univention.admin.modules.lookup( uvmm_profile, self.co, self.lo, scope='one', base = self.base, required = False, unique = False )
		except univention.admin.uexceptions.base, e:
			ud.debug( ud.ADMIN, ud.ERROR, 'UVMM/UDM: get_profiles: error while searching for template: %s' % str( e ) )
			return {}

		return res

if __name__ == '__main__':
	udm = Client()
	print udm.get_profiles()
