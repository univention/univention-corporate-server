#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager
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

from univention.lib.i18n import Translation

import univention.admin.uldap
import univention.admin.modules
import univention.admin.handlers.uvmm.profile as uvmm_profile

from univention.management.console.log import MODULE
from univention.management.console.config import ucr

_ = Translation('univention.management.console.handlers.uvmm').translate

class LDAP_ConnectionError( Exception ):
	pass

# decorators
def ensureLDAP_Connection_Admin( func ):
	return ensureLDAP_Connection( func, 'admin' )

def ensureLDAP_Connection_Machine( func ):
	return ensureLDAP_Connection( func, 'machine' )

class ensureLDAP_Connection( object ):
	'''A decorator that creates an LDAP connection and sets class
	attributes to access it from within the class method:

	ldap_conn: univention.uldap.access object
	ldap_pos: univention.uldap.position object

	for class methods:
	class Test():
		@classmethod
		@ensureLDAP_Connection
		def do_ldap_stuff( self, bla ):
			self.ldap_conn ...

	for global functions:
	@ensureLDAP_Connection
	def do_ldap_stuff( bla ):
		do_ldap_stuff.ldap_conn ...
	'''
	def __init__( self, f, account ):
		self.f = f
		self.account = account

	def open( self, klass ):
		# LDAP connection already open?
		if hasattr( klass, 'ldap_conn' ) and klass.ldap_conn:
			return True

		host = ucr.get( 'ldap/server/name' )
		base = ucr.get( 'ldap/base' )
		if self.account == 'machine':
			pwfile = '/etc/machine.secret'
			binddn = ucr.get( 'ldap/hostdn' )
		elif self.account == 'admin':
			pwfile = '/etc/ldap.secret'
			binddn = 'cn=admin,%s' % base
		bindpw = open( pwfile ).read()
		if bindpw[ -1 ] == '\n':
			bindpw = bindpw[ 0 : -1 ]

		klass.ldap_conf = None
		try:
			klass.ldap_conn = univention.admin.uldap.access( host = host, base = base, binddn = binddn, bindpw = bindpw )
		except:
			klass.ldap_conn = None
			raise LDAP_ConnectionError()

		klass.ldap_pos = univention.admin.uldap.position( klass.ldap_conn.base )

		return True

	def __call__( self, *args, **kwargs ):
		klass = args[ 0 ]
		if not isinstance( klass, type ):
			klass = self
		self.open( klass )
		try:
			return self.f( *args, **kwargs )
		except univention.admin.uexceptions.base, e:
			# try to reopen connection
			klass.ldap_conn = None
			self.open( klass )
			try:
				return self.f( *args, **kwargs )
			except univention.admin.uexceptions.base, e:
				raise LDAP_ConnectionError( str( e ) )

class Client( object ):
	PROFILE_RDN = 'cn=Profiles,cn=Virtual Machine Manager'

	@classmethod
	def _tech_filter( self, tech ):
		if tech:
			# FIXME: we need a way to make things unique e.g. kvm == qemu
			if tech == 'qemu':
				tech = 'kvm'
			filter='univentionVirtualMachineProfileVirtTech=%s*' % tech
		else:
			filter='univentionVirtualMachineProfileVirtTech=*'
		return filter

	@classmethod
	@ensureLDAP_Connection_Machine
	def get_profiles( self, tech = None ):
		base = "%s,%s" % ( Client.PROFILE_RDN, self.ldap_pos.getDn() )
		res = univention.admin.modules.lookup( uvmm_profile, self.ldap_conf, self.ldap_conn, scope='sub', filter=self._tech_filter(tech), base = base, required = False, unique = False )

		return res

	@classmethod
	@ensureLDAP_Connection_Machine
	def get_profile( self, name, tech ):
		name = name.replace( '(', '\(' )
		name = name.replace( ')', '\)' )
		filter = '(&(%s)(cn=%s))' % (self._tech_filter(tech), name)
		base = "%s,%s" % ( Client.PROFILE_RDN, self.ldap_pos.getDn() )
		res = univention.admin.modules.lookup( uvmm_profile, self.ldap_conf, self.ldap_conn, filter = filter, scope='sub', base = base, required = False, unique = True )

		ud.debug( ud.ADMIN, ud.ERROR, 'UVMM/UDM: get_profile: profile: %s' % str( res ) )
		return res[ 0 ]

if __name__ == '__main__':
	udm = Client()
	print udm.get_profiles()
