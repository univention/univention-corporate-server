# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  wrapper around univention.license that translates error codes to exceptions
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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

import operator
import types
import univention.license
import univention.debug
import univention.admin.modules
import univention.admin.uexceptions
import univention.admin.localization
import univention.admin.license_data as licenses

translation=univention.admin.localization.translation('univention/admin')
_=translation.translate

_license = None

class License( object ):
	( CLIENT, ACCOUNT, DESKTOP, GROUPWARE ) = range( 4 )
	SYSACCOUNTS = 5
	def __init__( self ):
		if _license:
			raise 'never create this object directly'
		self.new_license = False
		self.disable_add = 0
		self._expired = False
		self.types= []
		self.licenses = {
				License.CLIENT : None, License.ACCOUNT : None,
				License.DESKTOP : None, License.GROUPWARE : None,
			}
		self.real = {
			License.CLIENT : 0,	License.ACCOUNT : 0,
			License.DESKTOP : 0, License.GROUPWARE : 0,
			}
		self.names = {
			License.CLIENT : 'Clients',	License.ACCOUNT : 'Accounts',
			License.DESKTOP : 'Desktops', License.GROUPWARE : 'Groupware Accounts',
			}
		self.keys = {
			License.ACCOUNT:   'univentionLicenseAccounts',
			License.CLIENT:    'univentionLicenseClients',
			License.DESKTOP:   'univentionLicenseuniventionDesktops',
			License.GROUPWARE: 'univentionLicenseGroupwareAccounts'
			}
		self.filters = {
			License.CLIENT : '(|(objectClass=univentionThinClient)(objectClass=univentionClient)(objectClass=univentionMobileClient)(objectClass=univentionWindows)(objectClass=univentionMacOSClient))',
			License.ACCOUNT : '(&(|(&(objectClass=posixAccount)(objectClass=shadowAccount))(objectClass=sambaSamAccount)(objectClass=univentionMail))(!(uidNumber=0))(!(uid=*$)))',
			License.DESKTOP :'(|(objectClass=univentionThinClient)(&(objectClass=univentionClient)(objectClass=posixAccount))(objectClass=univentionMobileClient))',
			License.GROUPWARE : '(&(objectclass=kolabInetOrgPerson)(kolabHomeServer=*))',
		}
		self.__selected = False

	def select( self, module ):
		if not self.__selected:
			self.error = univention.license.select( module )
			self.__raiseException()
			self.__selected = True

	def isValidFor( self, module ):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,
				'LICENSE: check license for module %s, "%s"' % ( module, str( self.types ) ) )
		if licenses.modules.has_key( module ):
			mlics = licenses.modules[ module ]
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,
					'LICENSE: module license: %s' % str( mlics ) )
			# empty list -> valid
			return mlics.valid( self.types )
		# unknown modules are always valid (e.g. customer modules)
		return True

	def modifyOptions( self, mod ):
		if licenses.modules.has_key( mod ):
			opts = licenses.modules[ mod ].options( self.types )
			if opts:
				module = univention.admin.modules.modules[ mod ]
				if module and hasattr( module, 'options' ):
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,
							'modifyOptions: %s' % str( opts ) )
					for opt, val in opts:
						if callable(val):
							val = val(self)
						if operator.isSequenceType(val):
							module.options[ opt ].disabled, module.options[ opt ].default = val
						else:
							default = val
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,
								'modifyOption: %s, %d, %d' % ( str( opt ), module.options[ opt ].disabled, module.options[ opt ].default ) )

	def checkModules( self ):
		deleted_mods = []
		for mod in univention.admin.modules.modules.keys():
			# remove module if valid license is missing
			if self.isValidFor( mod ):
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,
						'update: License is valid for module %s!!' % mod )
				# check module options according to given license type
				self.modifyOptions( mod )
			else:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,
						'update: License is NOT valid for module %s!!' % mod )
				del univention.admin.modules.modules[ mod ]
				deleted_mods.append( mod )

		# remove child modules that were deleted because of an invalid license
		for name, mod in univention.admin.modules.modules.items():
			if hasattr( mod, 'childmodules' ):
				new = []
				for child in mod.childmodules:
					if child in deleted_mods: continue
					new.append( child )
				mod.childmodules = new

		# remove operations for adding or modifying if license is expired
		if self._expired:
			for name, mod in univention.admin.modules.modules.items():
				if hasattr( mod, 'operations' ):
					try:
						mod.operations.remove( 'add' )
						mod.operations.remove( 'edit' )
					except: pass


	def __cmp_gt( self, val1, val2 ):
		return self.compare(val1, val2) == 1

	def __cmp_eq( self, val1, val2 ):
		return self.compare(val1, val2) == 0

	def compare(self, val1, val2):
		if val1 == 'unlimited' and val2 == 'unlimited':
			return 0
		if val1 == 'unlimited':
			return 1
		if val2 == 'unlimited':
			return -1
		return cmp(int(val1), int(val2))

	def init_select( self, lo, module ):
		self.select( module )
		self.__readLicense()
		disable_add = 0

		if self.new_license:
			self.__countObject( License.ACCOUNT, lo )
			self.__countObject( License.CLIENT, lo )
			self.__countObject( License.DESKTOP, lo )
			self.__countObject( License.GROUPWARE, lo )
			lic = ( self.licenses[License.CLIENT],
				self.licenses[License.ACCOUNT],
				self.licenses[License.DESKTOP],
				self.licenses[License.GROUPWARE] )
			real= ( self.real[License.CLIENT],
				self.real[License.ACCOUNT],
				self.real[License.DESKTOP],
				self.real[License.GROUPWARE] )
			disable_add = self.checkObjectCounts(lic, real)
			if disable_add: self._expired = True

			if not disable_add:
				license_base = univention.license.getValue ( 'univentionLicenseBaseDN' )
				if license_base == 'Free for personal use edition':
					disable_add=5

		# check modules list for validity and accepted operations
		self.checkModules()

		return disable_add

	def checkObjectCounts(self, lic, real):
		disable_add = 0
		lic_client, lic_account, lic_desktop, lic_groupware = lic
		real_client, real_account, real_desktop, real_groupware = real
		if lic_client and lic_account:
			if self.__cmp_gt( lic_client, lic_account ) and self.__cmp_gt( real_client, lic_client ):
				disable_add = 1
			elif self.__cmp_gt( lic_account, lic_client ) and self.__cmp_gt( int( real_account ) - License.SYSACCOUNTS, lic_account ):
				disable_add = 2
			elif self.__cmp_eq(lic_client, lic_account):
				if self.__cmp_gt( real_client, lic_client ):
					disable_add = 1
				elif self.__cmp_gt( int( real_account ) - License.SYSACCOUNTS, lic_account ):
					disable_add = 2
		else:
			if lic_client and self.__cmp_gt( real_client, lic_client ):
				disable_add = 1
			if lic_account and self.__cmp_gt( int( real_account ) - License.SYSACCOUNTS ,lic_account ):
				disable_add = 2
		if lic_desktop:
			if real_desktop and self.__cmp_gt( real_desktop, lic_desktop ):
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'LICENSE: 3')
				disable_add = 3
		if lic_groupware:
			if real_groupware and self.__cmp_gt( real_groupware, lic_groupware ):
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'LICENSE: 4')
				disable_add = 4
		return disable_add

	def __countObject( self, obj, lo ):
		if self.licenses[ obj ] and not self.licenses[ obj ] == 'unlimited':
			result = lo.searchDn( filter = self.filters[ obj ] )
			if result == None:
				self.real[ obj ] = 0
			else:
				self.real[ obj ] = len( result )
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,
					'LICENSE: Univention %s real %d' % ( self.names[ obj ], self.real[ obj ] ) )
		else:
			self.real[ obj ] = 0


	def __raiseException( self ):
		if self.error != 0:
			if self.error == -1:
				raise univention.admin.uexceptions.licenseNotFound
			elif self.error == 2:
				raise univention.admin.uexceptions.licenseExpired
			elif self.error == 4:
				raise univention.admin.uexceptions.licenseWrongBaseDn
			else:
				raise univention.admin.uexceptions.licenseInvalid

	def __getValue( self, key, default, name= '', errormsg = '' ):
		try:
			value = univention.license.getValue( key )
			self.new_license = True
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,
					'LICENSE: Univention %s allowed %s' % ( name, str( value ) ) )
		except:
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO,
					'LICENSE: %s' % errormsg )
			value = default

		univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'LICENSE: %s = %s' % ( name, value ) )
		return value

	def __readLicense( self ):
		self.licenses[ License.ACCOUNT ] = self.__getValue( self.keys[License.ACCOUNT], None,
				'Accounts', 'Univention Accounts not found' )
		self.licenses[ License.CLIENT ] = self.__getValue( self.keys[License.CLIENT], None,
				'Clients', 'Univention Clients not found' )
		self.licenses[ License.DESKTOP ] = self.__getValue( self.keys[License.DESKTOP], 2,
				'Desktops', 'Univention Desktops not found' )
		self.licenses[ License.GROUPWARE ] = self.__getValue( self.keys[License.GROUPWARE], 2,
				'Groupware Accounts', 'Groupware not found' )
		# if no type field is found it must be an old UCS license (<=1.3-0)
		self.types = self.__getValue( 'univentionLicenseType', [ 'UCS' ],
				'License Type', 'Type attribute not found' )
		if not isinstance( self.types, ( list, tuple ) ):
			self.types = [ self.types ]

_license = License()

# for compatibility
select = _license.select
init_select = _license.init_select
is_valid_for = _license.isValidFor
