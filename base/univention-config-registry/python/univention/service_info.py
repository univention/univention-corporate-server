# -*- coding: utf-8 -*-
#
# Univention Configuration Registry
#  Service information: read information about registered Config Registry
#  variables
#
# Copyright 2007-2015 Univention GmbH
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

import locale
import os
import re
import string
import shlex

import univention.info_tools as uit

class Service( uit.LocalizedDictionary ):
	def __init__( self ):
		uit.LocalizedDictionary.__init__( self )
		self.start_runlevel = []
		self.stop_runlevel = []
		self.start_code = 0
		self.stop_code = 0
		self.running = False

	def check( self ):
		"""Check service entry for validity, returning list of incomplete entries."""
		incomplete = []
		for key in ( 'description', 'programs' ):
			if not self.get( key, None ):
				incomplete.append(key)
		return incomplete

def pidof( name ):
	result = []
	for file in os.listdir( '/proc' ):
		dir = os.path.join( '/proc', file )
		if not os.path.isdir( dir ):
			continue
		if not os.path.isfile( os.path.join( dir, 'stat' ) ):
			continue
		cmdline = os.path.join( dir, 'cmdline' )
		if not os.path.isfile( cmdline ):
			continue
		fd = open( cmdline )
		cmd = fd.readline()
		# kernel thread
		if not cmd:
			continue
		if '\x00' in cmd: 
			args = cmd.split( '\x00' )
		else:
			args = cmd.split(' ')
		cmd = shlex.split( name )
		if cmd[0] in args:
			if len( cmd ) > 1 and len( args ) >= len( cmd ):
				for i in range( 1, len( cmd ) ):
					print cmd[ i ], args[ i ]
					if cmd[ i ] != args[ i ]:
						break
				else:
					result.append( file )
			else:
				result.append( file )

	return result

class ServiceInfo( object ):
	BASE_DIR = '/etc/univention/service.info'
	SERVICES = 'services'
	CUSTOMIZED = '_customized'
	FILE_SUFFIX = '.cfg'

	RUNLEVELS = map(str, range(7)) + ['S']
	INIT_SCRIPT_REGEX = re.compile( '(?P<action>[SK])(?P<code>[0-9]+)(?P<name>.*)' )

	def __init__( self, install_mode = False ):
		self.services = {}
		if not install_mode:
			self.__load_services()
			self.update_services()

	def sysv_infos( self ):
		global _runlevels, _init_link

		for level in _runlevels:
			for link in os.listdir( '/etc/rc%s.d/' % level ):
				if not os.path.islink( link ):
					continue
				matches = _init_link.match( link )
				if not matches:
					continue
				grp = matches.groupdict()

				name = grp.get( 'name', '' )
				if not name or not name in self.services.keys():
					continue
				if grp.get( 'action', '' ) == 'S':
					self.services[ name ].start_runlevels.append( level )
					self.services[ name ].start_code = int( grp[ 'code' ] )
				elif grp.get( 'action', '' ) == 'K':
					self.services[ name ].start_runlevels.append( level )
					self.services[ name ].start_code = int( grp[ 'code' ] )

	def __update_status( self, name, service ):
		for prog in service[ 'programs' ].split( ',' ):
			if prog and not pidof( prog.strip() ):
				service.running = False
				break
		else:
			service.running = True

	def update_services( self ):
		for name, serv in self.services.items():
			self.__update_status( name, serv )

	def check_services( self ):
		"""Return dictionary of incomplete service descriptions."""
		incomplete = {}
		for name, srv in self.services.items():
			miss = srv.check()
			if miss:
				incomplete[name] = miss
		return incomplete

	def write_customized( self ):
		filename = os.path.join( ServiceInfo.BASE_DIR, ServiceInfo.SERVICES,
								 ServiceInfo.CUSTOMIZED )
		try:
			fd = open( filename, 'w' )
		except:
			return False

		cfg = uit.UnicodeConfig()
		for name, srv in self.services.items():
			cfg.add_section( name )
			for key in var.keys():
				items = var.normalize( key )
				for item, value in items.items():
					cfg.set( name, item, value )

		cfg.write( fd )
		fd.close()

		return True

	def read_services( self, filename = None, package = None, override = False ):
		if not filename and not package:
			raise AttributeError( "neither 'filename' nor 'package' is specified" )
		if not filename:
			filename = os.path.join( ServiceInfo.BASE_DIR, ServiceInfo.SERVICES,
									 package + ServiceInfo.FILE_SUFFIX )
		cfg = uit.UnicodeConfig()
		cfg.read( filename )
		for sec in cfg.sections():
			# service already known?
			if not override and sec in self.services.keys():
				continue
			srv = Service()
			for name, value in cfg.items( sec ):
				srv[ name ] = value
			for path in srv.get('programs', '').split(','):
				# "programs" defines the "/proc/self/cmdline" of the service,
				# not the executable, therefore we test for a leading "/":
				# check if it is a real file    split to remove parameters
				if path.startswith('/') and not os.path.exists(path.split(' ', 1)[0]):
					break # ==> do not execute else
			else:
				self.services[ sec ] = srv

	def __load_services( self ):
		path = os.path.join( ServiceInfo.BASE_DIR, ServiceInfo.SERVICES )
		for entry in os.listdir( path ):
			# customized service descrptions are read afterwards
			if entry == ServiceInfo.CUSTOMIZED:
				continue
			cfgfile = os.path.join( path, entry )
			if os.path.isfile( cfgfile ):
				self.read_services( cfgfile )
		# read modified/added service descriptions
		self.read_customized()

	def read_customized( self ):
		custom = os.path.join( ServiceInfo.BASE_DIR, ServiceInfo.SERVICES,
							   ServiceInfo.CUSTOMIZED )
		self.read_services( custom, override = True )

	def get_services( self ):
		'''returns a list fo service names'''
		return self.services.keys()

	def get_service( self, name ):
		'''returns a service object associated with the given name or
		None if it does not exist'''
		self.services.get( name, None )

	def add_service( self, name, service ):
		'''this methods adds a new service object or overrides an old
		entry'''
		if not service.check():
			self.services[ name ] = service
