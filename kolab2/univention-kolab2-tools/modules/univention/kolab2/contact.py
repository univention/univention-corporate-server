#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention LDAP addressbook synchronisation
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

from object import Kolab2Object

class Kolab2Contact( Kolab2Object ):
	def __init__( self ):
		Kolab2Object.__init__( self, Kolab2Object.CONTACT )
		self.__attached = False

	def parse( self, data ):
		Kolab2Object.parse( self, data )
		phones = self._doc.getElementsByTagName( 'phone' )
		self.n_phones = 1
		for phone in phones:
			self._define_element( 'type', prefix = 'phone%d' % self.n_phones, parent = phone )
			self._define_element( 'number', prefix = 'phone%d' % self.n_phones, parent = phone )
			self.n_phones +=1

	def create( self ):
		Kolab2Object.create( self )

		# name
		elem = self._doc.createElement( 'name' )
		self._create_element( 'given-name', parent = elem, prefix = 'name' )
		self._create_element( 'last-name', parent = elem, prefix = 'name' )
		self._create_element( 'full-name', parent = elem, prefix = 'name' )
		self._doc.documentElement.appendChild( elem )

		# organization
		for item in ( 'organization', 'department', 'office-location', 'profession', 'job-title',
					  'manager-name', 'assistant', 'birthday' ):
			self._create_element( item, parent = self._doc.documentElement )

		# addresses
		for addr in ( 'home', 'business' ):
			elem = self._doc.createElement( 'address' )
			self._create_element( 'type', text = addr, parent = elem, prefix = addr )
			self._create_element( 'street', parent = elem, prefix = addr )
			self._create_element( 'locality', parent = elem, prefix = addr )
			self._create_element( 'region', parent = elem, prefix = addr )
			self._create_element( 'postal-code', parent = elem, prefix = addr )
			self._create_element( 'country', parent = elem, prefix = addr )
			self._doc.documentElement.appendChild( elem )

		# phone numbers
		for phone in ( 'business1', 'businessfax', 'home1', 'mobile' ):
			elem = self._doc.createElement( 'phone' )
			self._create_element( 'type', text = phone, parent = elem, prefix = phone )
			self._create_element( 'number', parent = elem, prefix = phone )
			self._doc.documentElement.appendChild( elem )

	def add_email_addresses(  self, display, addresses ):
		i = 0
		ignore = cfgRegistry.get( 'ldap/addressbook/sync/mail/ignore', '' )
		for addr in addresses:
			# email address
			if fnmatch.fnmatch( addr, ignore ):
				continue
			elem = self._doc.createElement( 'email' )
			self._create_element( 'display-name', text = display, parent = elem, prefix = 'email%d' % i )
			self._create_element( 'smtp-address', text = addr, parent = elem, prefix = 'email%d' % i )
			self._doc.documentElement.appendChild( elem )
			i += 1

	def __str__( self ):
		self.create_message()
		return self.as_string()

	def create( self ):
		Kolab2Object.create( self )
		# TODO: to be implemented

