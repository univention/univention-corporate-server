# -*- coding: utf-8 -*-
#
# Univention Management Console
#  web interface: main ldap connection
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

import ldap

import univention_baseconfig
import univention.uldap
import univention.debug as ud

class LdapConnection:
	__lo = None
	__basedn = ''
	__binddn = ''
	__bindpw = ''

	def __init__(self):
		if not LdapConnection.__lo:
			self.connect()

	def get_basedn(self):
		return LdapConnection.__basedn

	def get_binddn(self):
		return LdapConnection.__binddn

	def __nonzero__( self ):
		return LdapConnection.__lo != None

	def __getattr__(self, attr):
		""" Delegate access to implementation """
		return getattr(LdapConnection.__lo, attr)


	def __setattr__(self, attr, value):
		""" Delegate access to implementation """
		return setattr(LdapConnection.__lo, attr, value)


	def connected(self):
		return (LdapConnection.__lo != None)


	def connect( self, host = None, port = 389, binddn = '', bindpw = '', base = None, start_tls=2 ):

		baseConfig = univention_baseconfig.baseConfig()
		baseConfig.load()

		if not host:
			host = baseConfig[ 'ldap/server/name' ]
		if not base:
			base = baseConfig[ 'ldap/base' ]

		LdapConnection.__base = base

		try:
			LdapConnection.__lo = univention.uldap.access(host, port, base, binddn, bindpw, start_tls)
		except ldap.INVALID_CREDENTIALS,ex:
			LdapConnection.__lo = None
			ud.debug( ud.LDAP, ud.ERROR, 'ldapconn: authentication failed' )
		except ldap.UNWILLING_TO_PERFORM,ex:
			LdapConnection.__lo = None
			ud.debug( ud.LDAP, ud.ERROR, 'ldapconn: authentication failed' )
		except:
			LdapConnection.__lo = None
			ud.debug( ud.LDAP, ud.ERROR, 'ldapconn: unable to get ldap connection' )
		if LdapConnection.__lo:
			ud.debug( ud.LDAP, ud.INFO, 'ldapconn: got new connection to ldap server (binddn="%s")' % binddn )
			LdapConnection.__binddn = binddn
			LdapConnection.__bindpw = bindpw

	def disconnect( self ):
		if self:
			LdapConnection.__lo.lo.unbind()
			LdapConnection.__lo = None
