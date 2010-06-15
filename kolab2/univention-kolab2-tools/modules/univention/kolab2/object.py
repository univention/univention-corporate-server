#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Kolab2 Tools
#
# Copyright (C) 2008-2009 Univention GmbH
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

import datetime
import time
import xml.dom.minidom

import univention.debug as ud
import univention.config_registry as ucr

cfgRegistry = ucr.ConfigRegistry()
cfgRegistry.load()
_options = None

class Kolab2Object( object ):
	CONTACT, EVENT = range( 2 )
	PRODUCT_ID = 'Univention Kolab2 Tools'
	_document_types = { CONTACT : 'contact',
						EVENT : 'event' }

	def __init__( self, type ):
		self._type = type

	def is_contact( self ):
		return self._type == Kolab2Object.CONTACT

	def is_event( self ):
		return self._type == Kolab2Object.EVENT

	def parse( self, data ):
		self._doc = xml.dom.minidom.parseString( data )

		self._define_element( 'uid' )
		self._define_element( 'body' )
		self._define_element( 'categories' )
		self._define_element( 'creation-date' )
		self._define_element( 'last-modification-date' )
		self._define_element( 'sensitivity' )
		self._define_element( 'product-id' )

	def modified( self ):
		now = datetime.datetime.utcnow()
		iso = now.isoformat()
		self.last_modification_date = '%sZ' % iso[ : iso.rfind( '.' ) ]
		self.product_id = Kolab2Object.PRODUCT_ID

	def create( self, product = PRODUCT_ID ):
		uid = '%s@%s.%s' % ( time.time(), cfgRegistry.get( 'hostname', '' ),
							 cfgRegistry.get( 'domainname', '' ) )

		# create document
		implement = xml.dom.getDOMImplementation()
		tag = Kolab2Object._document_types[ document_type ]
		self._doc = implement.createDocument( None, tag , None )

		# id
		self._create_element( 'uid', uid, self._doc.documentElement )

		# creation and modification date
		now = datetime.datetime.now()
		self._create_element( 'creation-date', text = now.isoformat(),
							   parent = self._doc.documentElement )
		self._create_element( 'last-modification-date', text = now.isoformat(),
							   parent = self._doc.documentElement )

		# sensitivity
		self._create_element( 'sensitivity', text = 'public', parent = self._doc.documentElement )

		# product name
		self._create_element( 'product-id', text = product, parent = self._doc.documentElement )

	def _define_element( self, name, attr = None, prefix = '', parent = None ):
		if not attr:
			attr = name.replace( '-', '_' )
		if prefix:
			attr = prefix + '_' + attr

		if parent:
			elems = parent.getElementsByTagName( name )
		else:
			elems = self._doc.getElementsByTagName( name )
		if elems:
			children = elems[ 0 ].childNodes
			if children:
				object.__setattr__( self, attr, children[ 0 ] )
			else:
				object.__setattr__( self, attr, '' )
		else:
			object.__setattr__( self, attr, '' )

	def _create_element( self, name, text = '', parent = None, prefix = None ):
		if prefix:
			attr_name = prefix + '_' + name
		else:
			attr_name = name
		attr_name = attr_name.replace( '-', '_' )
		setattr( self, attr_name, self._doc.createTextNode( text ) )
		elem = self._doc.createElement( name )
		elem.appendChild( getattr( self, attr_name ) )
		if parent:
			parent.appendChild( elem )

	def __setattr__( self, attr, value ):
		'''Support setting the kolab object attributes directly via <object>.<attribute>'''

		if hasattr( self, attr ) and isinstance( object.__getattribute__( self, attr ), xml.dom.Node ):
			object.__getattribute__( self, attr ).data = value
		else:
			object.__setattr__( self, attr, value )

	def __getattribute__( self, attr ):
		'''Support setting the kolab object attributes directly via <object>.<attribute>'''

		if hasattr( self, attr ) and isinstance( object.__getattribute__( self, attr ), xml.dom.minidom.Text ):
			return object.__getattribute__( self, attr ).data
		else:
			return object.__getattribute__( self, attr )

	def as_string( self ):
		return self._doc.toxml( encoding = 'utf-8' )
