#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMC ACL implementation
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

import os, sys, ldap, re
import cPickle

import univention.debug as ud

import univention.management.console as umc

import univention.admin.modules
import univention.admin.handlers.computers.domaincontroller_master as dc_master
import univention.admin.handlers.computers.domaincontroller_backup as dc_backup
import univention.admin.handlers.computers.domaincontroller_slave as dc_slave
import univention.admin.handlers.computers.memberserver as memberserver
import univention.admin.handlers.computers.managedclient as managedclient
import univention.admin.handlers.computers.mobileclient as mobileclient

class ACLs:
	# constants
	( MATCH_NONE, MATCH_PART, MATCH_FULL ) = range( 3 )

	_systemroles = ( dc_master, dc_backup, dc_slave, memberserver, managedclient, mobileclient )

	def __init__( self, ldap_base = None, acls = None ):

		self.__ldap_base = ldap_base
		# the main acl dict
		if not acls:
			self.acls = { 'allow': [ ], 'disallow': [ ] }
		else:
			self.acls = acls

		# internal cache for the hosts
		self.__cache = { }

	def _expand_hostlist( self, hostlist ):
		hosts = [ ]
		if not self.__ldap_base:
			if umc.baseconfig.has_key( 'ldap/base' ):
				self.__ldap_base = umc.baseconfig[ 'ldap/base' ]

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

				if servers:
					for server in servers:
						if server.has_key( 'name' ):
							hosts.append( server[ 'name' ] )

			elif host.startswith( 'service:' ):
				host = host[ len( 'service:' ) : ]
				for role in ACLs._systemroles:
					servers += role.lookup( None, self.lo, 'univentionService=%s' % host, base=self.__ldap_base )

				if servers:
					for server in servers:
						if server.has_key( 'name' ):
							hosts.append( server[ 'name' ] )

			elif host == '*':
				if not self.__cache.has_key( self.__ldap_base ):
					self.__cache[ self.__ldap_base ] = [ ]

					for role in ACLs._systemroles:
						servers += role.lookup( None, self.lo, None, base=self.__ldap_base )

					if servers:
						for server in servers:
							if server.has_key( 'name' ):
								hosts.append( server[ 'name' ] )
								self.__cache[ self.__ldap_base ].append( server[ 'name' ] )
				else:
					hosts += self.__cache[ self.__ldap_base ]

			else:
				for role in ACLs._systemroles:
					servers += role.lookup( None, self.lo, 'cn=%s' % host, base=self.__ldap_base )

				if servers:
					for server in servers:
						if server.has_key( 'name' ):
							hosts.append( server[ 'name' ] )

		return hosts

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
		return ( command, options )

	def __append( self, right, left, fromUser, object ):
		for host in self._expand_hostlist( object.get( 'univentionConsoleACLHost', [ '*' ] ) ):
			for command in object.get( 'univentionConsoleACLCommand', '' ):
				command, options = self.__parse_command( command )
				if fromUser:
					# we do not check if the group already has disallowed the command, because first we will append the user rules
					self.acls[ right ].append( { 'fromUser': True, 'host': host, 'command': command, 'options': options } )
				else:
					# if we append a group allow rule, then we check if the command was disallowed by the user
					append_rule = True
					for acl in self.acls[ left ]:
						if acl[ 'fromUser' ]:
							if acl[ 'host' ] == host:
								if self.__command_match( acl[ 'command' ], command ) and self.__option_match( acl[ 'options' ], options ):
									append_rule = False
					if append_rule:
						self.acls[ 'allow' ].append( { 'fromUser': False, 'host': host, 'command': command, 'options': options } )

	def _append_allow( self, fromUser, object ): #fromUser, host, command, data ):
		self.__append( 'allow', 'disallow', fromUser, object )

	def _append_disallow( self, fromUser, object ): #fromUser, host, command, data ):
		self.__append( 'disallow', 'allow', fromUser, object )

	def __compare_rules( self, rule1, rule2 ):
		# return the major rule

		if not rule1:
			return rule2
		if not rule2:
			return rule1

		if rule1[ 'fromUser' ] and not rule2[ 'fromUser' ]:
			return rule1
		elif not rule1[ 'fromUser' ] and rule2[ 'fromUser' ]:
			return rule2
		else:
			if len( rule1[ 'command' ] ) >= len( rule2[ 'command' ] ):
				return rule1
			else:
				return rule2

	def __option_match( self, opt_pattern, opts ):
		match = ACLs.MATCH_FULL
		for key, value in opt_pattern.items():
			if opts.has_key( key ):
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
		# if cmd1 == cmd2 return self.COMMAND_MATCH
		# if cmd2 is part od cmd1 return self.COMMAND_PART
		# if noting return self.COMMAND_NONE

		if cmd1 == cmd2:
			return ACLs.MATCH_FULL

		if cmd1[ -1 ] == '*':
			if cmd2.startswith( cmd1[ 0:-2 ] ):
				return ACLs.MATCH_PART

		return ACLs.MATCH_NONE

	def is_command_allowed( self, command, hostname = None, options = {} ):
		if not hostname:
			hostname = umc.baseconfig[ 'hostname' ]
		# first check if the command is disallowed and then check if an other rule is more important
		disallowed_rule = False
		for disallow in self.acls[ 'disallow' ]:
			if disallow[ 'host' ] == hostname:
				match = self.__command_match( disallow[ 'command' ], command )
				if not match in ( ACLs.MATCH_FULL, ACLs.MATCH_PART ):
					continue
				opt_match = self.__option_match( disallow[ 'options' ], options )
				if match == ACLs.MATCH_FULL and opt_match == ACLs.MATCH_FULL:
					if disallow[ 'fromUser' ]:
						# here we can exit
						return False
					else:
						disallowed_rule = self.__compare_rules( disallowed_rule, disallow )
				elif match == ACLs.MATCH_PART or opt_match == ACLs.MATCH_PART:
					disallowed_rule = self.__compare_rules( disallowed_rule, disallow )

		for allow in self.acls[ 'allow' ]:
			if not hostname or allow[ 'host' ] == hostname:
				match = self.__command_match( allow[ 'command' ], command )
				opt_match = self.__option_match( allow[ 'options' ], options )
				if match == ACLs.MATCH_FULL and opt_match == ACLs.MATCH_FULL:
					# if allow[ 'command' ] == command:
					if [ 'fromUser' ]:
						return True
					else:
						# check disallowed rule
						if self.__compare_rules( disallowed_rule, allow ) == allow:
							return True
				elif match == ACLs.MATCH_PART or opt_match == ACLs.MATCH_PART:
					if self.__compare_rules( disallowed_rule, allow ) == allow:
						return True

		return False

	def _dump( self ):
		ud.debug( ud.ADMIN, ud.PROCESS, '          %10s -- %20s -- %20s -- %20s' % ( 'fromUser', 'Host', 'Command', 'Options' ))
		ud.debug( ud.ADMIN, ud.PROCESS, '**********************************************************************************************')

		for allow in self.acls[ 'allow' ]:
			ud.debug( ud.ADMIN, ud.PROCESS, 'ALLOW:    %10s -- %20s -- %20s -- %20s' % ( allow[ 'fromUser' ], allow[ 'host' ], allow[ 'command' ], allow[ 'options' ] ))
		for disallow in self.acls[ 'disallow' ]:
			ud.debug( ud.ADMIN, ud.PROCESS, 'DISALLOW: %10s -- %20s -- %20s -- %20s' % ( disallow[ 'fromUser' ], disallow[ 'host' ], disallow[ 'command' ], disallow[ 'options' ] ))

	def _read_from_file( self, username ):
		filename = '/var/cache/univention-management-console/acls/%s' % username

		try:
			file = open( filename, 'r' )
		except IOError:
			return False

		lines = file.read( )
		self.acls = cPickle.loads( lines )
		file.close( )

	def _write_to_file( self, username ):
		filename='/var/cache/univention-management-console/acls/%s' % username

		file = os.open( filename, os.O_WRONLY | os.O_TRUNC | os.O_CREAT )
		os.write( file, cPickle.dumps( self.acls ) )
		os.close( file )

class ConsoleACLs ( ACLs ):

	def __init__( self, lo, username, ldap_base ):
		ACLs.__init__( self, ldap_base )
		self.lo = lo
		self.username = username

		self.FROM_USER=True
		self.FROM_GROUP=False

		if self.lo:
			self._read_from_ldap( )
			self._write_to_file( self.username )
		else:
			# read ACLs from file
			self._read_from_file ( self.username )

		self._dump()

	def _get_policy_for_dn( self, dn ):
		policy = self.lo.getPolicies( dn, policies=[ ], attrs={ }, result={ }, fixedattrs={ } )

		if policy.has_key( 'univentionPolicyConsoleAccess' ):
			return policy[ 'univentionPolicyConsoleAccess' ]
		return None


	def _read_from_ldap( self ):
		# TODO: check for fixed attributes
		userAllow = [ ]
		userDisallow = [ ]
		policy = self._get_policy_for_dn ( self.lo.binddn )
		if policy:
			if policy.has_key( 'univentionConsoleAllow' ):
				for value in policy[ 'univentionConsoleAllow' ][ 'value' ]:
					self._append_allow( self.FROM_USER, self.lo.get( value ) ) #value.split( ':' )[ 0 ], value.split( ':' )[ 1], value.split( ':' )[ 2] )
			if policy.has_key( 'univentionConsoleDisallow' ):
				for value in policy[ 'univentionConsoleDisallow' ][ 'value' ]:
					self._append_disallow( self.FROM_USER, self.lo.get( value ) ) #value.split( ':' )[ 0 ], value.split( ':' )[ 1], value.split( ':' )[ 2] )

		# TODO: check for neested groups

		groupDNs = self.lo.searchDn( filter='uniqueMember=%s' % self.lo.binddn )

		groupAllow = [ ]
		groupDisallow = [ ]
		for gDN in groupDNs:
			policy = self._get_policy_for_dn ( gDN )
			if policy:
				if policy.has_key( 'univentionConsoleAllow' ):
					groupAllow.append( policy[ 'univentionConsoleAllow' ][ 'value' ] )
					for value in policy[ 'univentionConsoleAllow' ][ 'value' ]:
						self._append_allow( self.FROM_GROUP, self.lo.get( value ) )
				if policy.has_key( 'univentionConsoleDisallow' ):
					for value in policy[ 'univentionConsoleDisallow' ][ 'value' ]:
						self._append_disallow( self.FROM_GROUP, self.lo.get( value ) )


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

	lo = univention.uldap.access( host = umc.baseconfig[ 'ldap/server/name' ], base = umc.baseconfig[ 'ldap/base' ], start_tls = 2 )
	userdn=lo.searchDn( filter = 'uid=%s' % username )
	if not userdn:
		print '\nError: user not found'
		sys.exit( 1 )

	userdn=userdn[ 0 ]

	try:
		lo = univention.uldap.access( host = umc.baseconfig[ 'ldap/server/name' ] , base = umc.baseconfig[ 'ldap/base' ], binddn = userdn, bindpw = password, start_tls = 2 )
	except ldap.INVALID_CREDENTIALS:
		print '\nError: invalid credentials'
		sys.exit( 1 )

	acls = ConsoleACLs( lo, username, umc.baseconfig[ 'ldap/base' ] )

	print 'is baseconfig/set/foo allowed on this host?: %s' % acls.is_command_allowed ( 'baseconfig/set/foo', umc.baseconfig[ 'hostname' ] )
	print 'is baseconfig/set     allowed on this host with data ldap/*?: %s' % acls.is_command_allowed ( 'baseconfig/set', umc.baseconfig[ 'hostname' ], { 'key' : 'ldap/*' } )
	print 'is baseconfig/set     allowed on this host with data net/bla?: %s' % acls.is_command_allowed ( 'baseconfig/set', umc.baseconfig[ 'hostname' ], { 'key' : 'net/bla' } )
	print 'is baseconfig/set     allowed on this host with data interfaces/eth1/address?: %s' % acls.is_command_allowed ( 'baseconfig/set', umc.baseconfig[ 'hostname' ], { 'key' : 'interfaces/eth1/address' } )
	print 'is baseconfig/get     allowed on this host?: %s' % acls.is_command_allowed ( 'baseconfig/get', umc.baseconfig[ 'hostname' ] )
	print 'is cups/view          allowed on this host?: %s' % acls.is_command_allowed ( 'cups/view', umc.baseconfig[ 'hostname' ] )
	print 'is foo/bar            allowed on this host?: %s' % acls.is_command_allowed ( 'foo/bar', umc.baseconfig[ 'hostname' ] )
