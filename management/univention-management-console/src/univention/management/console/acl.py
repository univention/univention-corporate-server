#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMC ACL implementation
#
# Copyright 2006-2012 Univention GmbH
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

import os, sys, ldap, re
import cPickle

from .config import ucr
from .log import *

import univention.admin.modules
import univention.admin.handlers.computers.domaincontroller_master as dc_master
import univention.admin.handlers.computers.domaincontroller_backup as dc_backup
import univention.admin.handlers.computers.domaincontroller_slave as dc_slave
import univention.admin.handlers.computers.memberserver as memberserver
import univention.admin.handlers.computers.managedclient as managedclient
import univention.admin.handlers.computers.mobileclient as mobileclient

class Rule( dict ):
	@property
	def fromUser( self ):
		return self.get( 'fromUser', False )

	@property
	def host( self ):
		return self.get( 'host', '*' )

	@property
	def command( self ):
		return self.get( 'command', '' )

	@property
	def options( self ):
		return self.get( 'options', {} )

	@property
	def flavor( self ):
		return self.get( 'flavor', None )

	def __eq__( self, other ):
		return self.fromUser == other.fromUser and self.host == other.host and self.command == other.command and self.flavor == other.flavor and self.options == other.options

class ACLs( object ):
	"""Provides methods to determine the access rights of users to
	specific UMC commands"""

	# constants
	( MATCH_NONE, MATCH_PART, MATCH_FULL ) = range( 3 )
	CACHE_DIR = '/var/cache/univention-management-console/acls'

	_systemroles = ( dc_master, dc_backup, dc_slave, memberserver, managedclient, mobileclient )

	def __init__( self, ldap_base = None, acls = None ):
		self.__ldap_base = ldap_base
		# the main acl dict
		if acls is None:
			self.acls = []
		else:
			self.acls = map( lambda x: Rule( x ), acls )

		# internal cache for the hosts
		self.__cache = {}

	def _expand_hostlist( self, hostlist ):
		hosts = []
		if self.__ldap_base is None:
			self.__ldap_base = ucr.get( 'ldap/base', None )

		servers = []
		for host in hostlist:
			if host.startswith( 'systemrole:' ):
				host = host[ len( 'systemrole:' ) : ]
				if host == 'domaincontroller_master':
					servers = dc_master.lookup( None, self.lo, None, base=self.__ldap_base )
				elif host == 'domaincontroller_backup':
					servers = dc_backup.lookup( None, self.lo, None, base=self.__ldap_base )
				elif host == 'domaincontroller_slave':
					servers = dc_slave.lookup( None, self.lo, None, base=self.__ldap_base )
				elif host == 'memberserver':
					servers = memberserver.lookup( None, self.lo, None, base=self.__ldap_base )
				elif host == 'mobileclient':
					servers = mobileclient.lookup( None, self.lo, None, base=self.__ldap_base )
				elif host == 'managedclient':
					servers = managedclient.lookup( None, self.lo, None, base=self.__ldap_base )

				hosts.extend( filter( lambda server: 'name' in server, servers ) )

			elif host.startswith( 'service:' ):
				host = host[ len( 'service:' ) : ]
				for role in ACLs._systemroles:
					servers += role.lookup( None, self.lo, 'univentionService=%s' % host, base=self.__ldap_base )

				hosts.extend( filter( lambda server: 'name' in server, servers ) )

			elif host == '*':
				if not self.__ldap_base in self.__cache:
					self.__cache[ self.__ldap_base ] = [ ]

					for role in ACLs._systemroles:
						servers += role.lookup( None, self.lo, None, base=self.__ldap_base )

						new_hosts = filter( lambda server: 'name' in server, servers )

					hosts.extend( new_hosts )
					self.__cache[ self.__ldap_base ].extend( new_hosts )
				else:
					hosts += self.__cache[ self.__ldap_base ]

			else:
				for role in ACLs._systemroles:
					servers += role.lookup( None, self.lo, 'cn=%s' % host, base=self.__ldap_base )

				hosts.extend( filter( lambda server: 'name' in server, servers ) )

		return map( lambda server: server[ 'name' ], hosts )

	def __parse_command( self, command ):
		if command.find( ':' ) != -1:
			data = command.split( ':' )[ 1 ]
			command = command.split( ':' )[ 0 ]
		else:
			data = [ ]

		options = {}
		if data:
			elements = data.split( ',' )
			for elem in elements:
				if elem.find( '=' ) != -1:
					key, value = elem.split( '=' )
					options[ key.strip() ] = value.strip()
				elif elem[ 0 ] == '!': # key without value allowed if starting with ! -> key may not exist
					options[ elem.strip() ] = None
		return ( command, options )

	def _append( self, fromUser, ldap_object ):
		for host in self._expand_hostlist( ldap_object.get( 'umcOperationSetHost', [ '*' ] ) ):
			flavor = ldap_object.get( 'umcOperationSetFlavor', [ '*' ] )
			for command in ldap_object.get( 'umcOperationSetCommand', '' ):
				command, options = self.__parse_command( command )
				new_rule = Rule( { 'fromUser': fromUser, 'host': host, 'command': command, 'options': options, 'flavor' : flavor[ 0 ] } )
				# do not add rule multiple times
				if not new_rule in self.acls:
					self.acls.append( new_rule )

	def __compare_rules( self, rule1, rule2 ):
		"""Hacky version of rule comparison"""

		if not rule1:
			return rule2
		if not rule2:
			return rule1

		if rule1.fromUser and not rule2.fromUser:
			return rule1
		elif not rule1.fromUser and rule2.fromUser:
			return rule2
		else:
			if len( rule1.command ) >= len( rule2.command ):
				return rule1
			else:
				return rule2

	def __option_match( self, opt_pattern, opts ):
		match = ACLs.MATCH_FULL
		for key, value in opt_pattern.items():
			# a key starting with ! means it may not be available
			if key[ 0 ] == '!' and key in opts:
				return ACLs.MATCH_NONE
			# else if key not not in opts no rule available -> OK
			if not key in opts:
				continue

			if isinstance( opts[ key ], basestring ):
				options = ( opts[ key ], )
			else:
				options = opts[ key ]
			for option in options:
				if not value[ -1 ] == '*':
					if value != option:
						return ACLs.MATCH_NONE
				elif not option.startswith( value[ : -1 ] ):
					return ACLs.MATCH_NONE
			else:
				match = ACLs.MATCH_FULL

		return match

	def __command_match( self, cmd1, cmd2 ):
		"""
		if cmd1 == cmd2 return self.COMMAND_MATCH
		if cmd2 is part of cmd1 return self.COMMAND_PART
		if noting return self.COMMAND_NONE
		"""
		if cmd1 == cmd2:
			return ACLs.MATCH_FULL

		if cmd1[ -1 ] == '*' and cmd2.startswith( cmd1[ : -1 ] ):
			return ACLs.MATCH_PART

		return ACLs.MATCH_NONE

	def __flavor_match( self, flavor1, flavor2 ):
		"""
		if flavor1 == flavor2  or flavor1 is None or the pattern '*' return self.COMMAND_MATCH
		if flavor2 is part of flavor1 return self.COMMAND_PART
		if noting return self.COMMAND_NONE
		"""
		if flavor1 == flavor2 or flavor1 is None or flavor1 == '*':
			return ACLs.MATCH_FULL

		if flavor1[ -1 ] == '*' and flavor2.startswith( flavor1[ : -1 ] ):
			return ACLs.MATCH_PART

		return ACLs.MATCH_NONE


	def _is_allowed( self, acls, command, hostname, options, flavor ):
		for rule in acls:
			if hostname and rule.host != '*' and rule.host != hostname:
				continue
			match = self.__command_match( rule.command, command )
			opt_match = self.__option_match( rule.options, options )
			flavor_match = self.__flavor_match( rule.flavor, flavor )
			if match in ( ACLs.MATCH_PART, ACLs.MATCH_FULL ) and opt_match == ACLs.MATCH_FULL and flavor_match in ( ACLs.MATCH_PART, ACLs.MATCH_FULL ):
				return True

		# default is to prohibited the command execution
		return False

	def is_command_allowed( self, command, hostname = None, options = {}, flavor = None ):
		if not hostname:
			hostname = ucr[ 'hostname' ]

		# first check the group rules. If the group policy allows the
		# command there is no need to check the user policy
		return self._is_allowed( filter( lambda x: x.fromUser == False, self.acls ), command, hostname, options, flavor ) or \
			   self._is_allowed( filter( lambda x: x.fromUser == True, self.acls ), command, hostname, options, flavor )

	def _dump( self ):
		"""Dumps the ACLs for the user"""
		ACL.process( 'Allowed UMC operations:' )
		ACL.process( ' %-5s | %-20s | %-15s | %-20s | %-20s' % ( 'User', 'Host', 'Flavor', 'Command', 'Options' ) )
		ACL.process( '******************************************************************************')
		for rule in self.acls:
			ACL.process( ' %-5s | %-20s | %-15s | %-20s | %-20s' % ( rule.fromUser, rule.host, rule.flavor, rule.command, rule.options ) )
		ACL.process( '' )

	def _read_from_file( self, username ):
		filename = os.path.join( ACLs.CACHE_DIR,  username )

		try:
			file = open( filename, 'r' )
		except IOError:
			return False

		lines = file.read( )
		acls = cPickle.loads( lines )
		file.close( )

		self.acls = []
		# check old format (< UCS 3.0)
		if isinstance( acls, dict ):
			for rule in acls[ 'allow' ]:
				rule = Rule( rule )
				if not rule in self.acls:
					rule.flavor = None
					self.acls.append( rule )
		else: # new format
			for rule in acls:
				if not rule in self.acls:
					if not 'flavor' in rule:
						rule[ 'flavor' ] = None
					if not 'options' in rule:
						rule[ 'options' ] = {}
					self.acls.append( rule )

	def _write_to_file( self, username ):
		filename = os.path.join( ACLs.CACHE_DIR,  username )

		file = os.open( filename, os.O_WRONLY | os.O_TRUNC | os.O_CREAT, 0600 )
		os.write( file, cPickle.dumps( self.acls ) )
		os.close( file )

	def json( self ):
		return self.acls

class LDAP_ACLs ( ACLs ):
	"""Reads ACLs from LDAP directory for the given username."""

	FROM_USER = True
	FROM_GROUP = False

	def __init__( self, lo, username, ldap_base ):
		ACLs.__init__( self, ldap_base )
		self.lo = lo
		self.username = username

		if self.lo:
			self._read_from_ldap( )
			self._write_to_file( self.username )
		else:
			# read ACLs from file
			self._read_from_file ( self.username )

		self._dump()

	def _get_policy_for_dn( self, dn ):
		policy = self.lo.getPolicies( dn, policies=[ ], attrs={ }, result={ }, fixedattrs={ } )

		return policy.get( 'umcPolicy', None )

	def _read_from_ldap( self ):
		# TODO: check for fixed attributes
		try:
			userdn = self.lo.searchDn( '(&(objectClass=person)(uid=%s))' % self.username, unique = True )[ 0 ]
			policy = self._get_policy_for_dn ( userdn )
		except ( ldap.LDAPError, IndexError ):
			# read ACLs from file
			self._read_from_file( self.username )
			return

		if policy and 'umcPolicyGrantedOperationSet' in policy:
			for value in policy[ 'umcPolicyGrantedOperationSet' ][ 'value' ]:
				self._append( LDAP_ACLs.FROM_USER, self.lo.get( value ) )

		# TODO: check for nested groups
		groupDNs = self.lo.searchDn( filter = 'uniqueMember=%s' % userdn )

		for gDN in groupDNs:
			policy = self._get_policy_for_dn ( gDN )
			if not policy:
				continue
			if 'umcPolicyGrantedOperationSet' in policy:
				for value in policy[ 'umcPolicyGrantedOperationSet' ][ 'value' ]:
					self._append( LDAP_ACLs.FROM_GROUP, self.lo.get( value ) )


if __name__ == '__main__':
	import univention
	import univention.uldap
	import getpass

	username = raw_input( 'Username [Administrator]: ' )
	if not username:
		username='Administrator'
	password = getpass.getpass( 'Password [univention]: ' )
	if not password:
		password='univention'

	lo = univention.uldap.access( host = ucr[ 'ldap/server/name' ], base = ucr[ 'ldap/base' ], start_tls = 2 )
	userdn=lo.searchDn( filter = 'uid=%s' % username )
	if not userdn:
		print '\nError: user not found'
		sys.exit( 1 )

	userdn=userdn[ 0 ]

	try:
		lo = univention.uldap.access( host = ucr[ 'ldap/server/name' ] , base = ucr[ 'ldap/base' ], binddn = userdn, bindpw = password, start_tls = 2 )
	except ldap.INVALID_CREDENTIALS:
		print '\nError: invalid credentials'
		sys.exit( 1 )

	acls = LDAP_ACLs( lo, username, ucr[ 'ldap/base' ] )

	print 'is baseconfig/set/foo allowed on this host?: %s' % acls.is_command_allowed ( 'baseconfig/set/foo', ucr[ 'hostname' ] )
	print 'is baseconfig/set     allowed on this host with data ldap/*?: %s' % acls.is_command_allowed ( 'baseconfig/set', ucr[ 'hostname' ], { 'key' : 'ldap/*' } )
	print 'is baseconfig/set     allowed on this host with data net/bla?: %s' % acls.is_command_allowed ( 'baseconfig/set', ucr[ 'hostname' ], { 'key' : 'net/bla' } )
	print 'is baseconfig/set     allowed on this host with data interfaces/eth1/address?: %s' % acls.is_command_allowed ( 'baseconfig/set', ucr[ 'hostname' ], { 'key' : 'interfaces/eth1/address' } )
	print 'is baseconfig/get     allowed on this host?: %s' % acls.is_command_allowed ( 'baseconfig/get', ucr[ 'hostname' ] )
	print 'is cups/view          allowed on this host?: %s' % acls.is_command_allowed ( 'cups/view', ucr[ 'hostname' ] )
	print 'is foo/bar            allowed on this host?: %s' % acls.is_command_allowed ( 'foo/bar', ucr[ 'hostname' ] )
