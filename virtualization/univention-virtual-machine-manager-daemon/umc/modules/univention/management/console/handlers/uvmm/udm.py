#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Virtual Machine Manager
#  module: UDM modules
#
# Copyright 2010 Univention GmbH
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
