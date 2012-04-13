# -*- coding: utf-8 -*-
#
# Univention Management Console
#  next generation of UMC modules
#
# Copyright 2011 Univention GmbH
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

import copy
import os
import sys
import xml.parsers.expat
import xml.etree.ElementTree as ET

from .tools import JSON_Object, JSON_List, JSON_Dict
from .log import RESOURCES

class Attribute( JSON_Object ):
	'''Represents an command attribute'''
	def __init__( self, name = '', syntax = '', required = True ):
		self.name = name
		self.syntax = syntax
		self.required = required

	def fromJSON( self, json ):
		for attr in ( 'name' , 'syntax', 'required' ):
			setattr( self, attr, json[ attr ] )

class Command( JSON_Object ):
	'''Represents an UMCP command handled by a module'''
	SEPARATOR = '/'

	def __init__( self, name = '', method = None, attributes = None ):
		self.name = name
		if method:
			self.method = method
		else:
			self.method = self.name.replace( Command.SEPARATOR, '_' )
		if attributes is None:
			self.attributes = JSON_List()
		else:
			self.attributes = attributes

	def fromJSON( self, json ):
		for attr in ( 'name' , 'method' ):
			setattr( self, attr, json[ attr ] )
		for attr in json[ 'attributes' ]:
			attribute = Attribute()
			attribute.fromJSON( attr )
			self.attributes.append( attribute )

class Flavor( JSON_Object ):
	'''Defines a flavor of a module. This provides another name and icon
	in the overview and may influence the behaviour of the module.'''
	def __init__( self, id = '', icon = '', name = '', description = '', overwrites = [] ):
		self.id = id
		self.name = name
		self.description = description
		self.icon = icon
		self.overwrites = overwrites

class Module( JSON_Object ):
	'''Represents an command attribute'''
	def __init__( self, id = '', name = '', description = '', icon = '', categories = None, flavors = None, commands = None ):
		self.id = id
		self.name = name
		self.description = description
		self.icon = icon
		if flavors is None:
			self.flavors = JSON_List()
		else:
			self.flavors = JSON_List( flavors )

		if categories is None:
			self.categories = JSON_List()
		else:
			self.categories = categories
		if commands is None:
			self.commands = JSON_List()
		else:
			self.commands = commands

	def fromJSON( self, json ):
		if isinstance( json, dict ):
			for attr in ( 'id', 'name' , 'description', 'icon', 'categories' ):
				setattr( self, attr, json[ attr ] )
			commands = json[ 'commands' ]
		else:
			commands = json
		for cmd in commands:
			command = Command()
			command.fromJSON( cmd )
			self.commands.append( command )

class XML_Definition( ET.ElementTree ):
	'''container for the interface description of a module'''
	def __init__( self, root = None, filename = None ):
		ET.ElementTree.__init__( self, element = root, file = filename )

	@property
	def name( self ):
		return self.find( 'module/name' ).text

	@property
	def description( self ):
		return self.find( 'module/description' ).text

	@property
	def id( self ):
		return self.find( 'module' ).get( 'id' )

	@property
	def notifier( self ):
		return self.find( 'module' ).get( 'notifier' )

	@property
	def icon( self ):
		return self.find( 'module' ).get( 'icon' )

	@property
	def flavors( self ):
		'''Retrieve list of flavor objects'''
		for elem in self.findall( 'module/flavor' ):
			flavor = Flavor( elem.get( 'id' ), elem.get( 'icon' ) )
			flavor.overwrites = elem.get( 'overwrites', '' ).split( ',' )
			flavor.name = elem.find( 'name' ).text
			flavor.description = elem.find( 'description' ).text
			yield flavor

	@property
	def categories( self ):
		return [ elem.get( 'name' ) for elem in self.findall( 'module/categories/category' ) ]

	def commands( self ):
		'''Generator to iterate over the commands'''
		for command in self.findall( 'module/command' ):
			yield command.get( 'name' )

	def get_module( self ):
		return Module( self.id, self.name, self.description, self.icon, self.categories, self.flavors )

	def get_flavor( self, name ):
		'''Retrieves details of a flavor'''
		for flavor in self.flavors:
			if flavor.name == name:
				cmd = Flavor( name, flavor.get( 'function' ) )
				return cmd

		return None

	def get_command( self, name ):
		'''Retrieves details of a command'''
		for command in self.findall( 'module/command' ):
			if command.get( 'name' ) == name:
				cmd = Command( name, command.get( 'function' ) )
				for elem in command.findall( 'attribute' ):
					attr = Attribute( elem.get( 'name' ), elem.get( 'syntax' ), elem.get( 'required' ) in ( '', "1" ) )
					cmd.attributes.append( attr )
				return cmd
		return None

_manager = None

class Manager( dict ):
	'''Manager of all available modules'''

	DIRECTORY = os.path.join( sys.prefix, 'share/univention-management-console/modules' )
	def __init__( self ):
		dict.__init__( self )

	def modules( self ):
		'''Return list of module names'''
		return self.keys()

	def load( self ):
		'''Load the list of available modules. As the list is cleared
		before, the method can also be used for reloading'''
		RESOURCES.info( 'Loading modules ...' )
		self.clear()
		for filename in os.listdir( Manager.DIRECTORY ):
			if not filename.endswith( '.xml' ):
				continue
			try:
				mod = XML_Definition( filename = os.path.join( Manager.DIRECTORY, filename ) )
				RESOURCES.info( 'Loaded module %s' % filename )
			except xml.parsers.expat.ExpatError, e:
				RESOURCES.warn( 'Failed to load module %s: %s' % ( filename, str( e ) ) )
				continue
			self[ mod.id ] = mod

	def permitted_commands( self, hostname, acls ):
		'''Retrieves a list of all modules and commands available
		according to the ACLs (instance of LDAP_ACLs)

		{ id : Module, ... }
		'''
		RESOURCES.info( 'Retrieving list of permitted commands' )
		modules = {}
		for module_id in self:
			mod = self[ module_id ].get_module()
			if not mod.flavors:
				flavors = [ Flavor( id = None ) ]
			else:
				flavors = copy.copy( mod.flavors )
			for flavor in flavors:
				at_least_one_command = False
				for command in self[ module_id ].commands():
					if acls.is_command_allowed( command, hostname, flavor = flavor.id ):
						if not module_id in modules:
							modules[ module_id ] = mod
						cmd = self[ module_id ].get_command( command )
						if not cmd in modules[ module_id ].commands:
							modules[ module_id ].commands.append( cmd )
						at_least_one_command = True

				# if there is not one command allowed with this flavor
				# it should not be shown in the overview
				if not at_least_one_command and mod.flavors:
					mod.flavors.remove( flavor )

			overwrites = set()
			for flavor in mod.flavors:
				overwrites.update( flavor.overwrites )

			mod.flavors = JSON_List( filter( lambda f: f.id not in overwrites, mod.flavors ) )

		return modules

	def module_providing( self, modules, command ):
		'''Searches a dictionary of modules (as returned by
		permitted_commands) for the given command. If found, the id of
		the module is returned, otherwise None'''
		RESOURCES.info( 'Searching for module providing command %s' % command )
		for module_id in modules:
			for cmd in modules[ module_id ].commands:
				if cmd.name == command:
					RESOURCES.info( 'Found module %s' % module_id )
					return module_id

		RESOURCES.info( 'No module provides %s' % command )
		return None

if __name__ == '__main__':
	mgr = Manager()
