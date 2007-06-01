#
# Univention Baseconfig
#  Service information: read information about registered Baseconfig
#  variables
#
# Copyright (C) 2007 Univention GmbH
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

import locale
import os
import re
import string

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
		for key in ( 'description', 'programs' ):
			if not self.get( key, None ):
				return False

		return True

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
		cmd = cmd.split( '\x00', 1 )[ 0 ]
		if cmd.endswith( name ):
			result.append( file )

	return result

class ServiceInfo( object ):
	BASE_DIR = '/etc/univention/service.info'
	SERVICES = 'services'
	CUSTOMIZED = '_customized'
	FILE_SUFFIX = '.cfg'

	RUNLEVELS = map( lambda x: str( x ), range( 0, 7 ) ) + [ 'S' ]
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
		failed = []
		for name, srv in self.services.items():
			if not srv.check():
				failed.append( name )
		return failed

	def read_services( self, filename ):
		cfg = uit.UnicodeConfig()
		cfg.read( filename )
		for sec in cfg.sections():
			# service already known?
			cat_name = string.lower( sec )
			if cat_name in self.services.keys():
				continue
			serv = Service()
			for name, value in cfg.items( sec ):
				serv[ name ] = value
			self.services[ cat_name ] = serv

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
		if service.check():
			self.services[ name ] = service
