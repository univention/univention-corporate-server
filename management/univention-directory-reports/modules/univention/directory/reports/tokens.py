# -*- coding: utf-8 -*-
#
# Univention Directory Reports
#  token classes
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

class Token( object ):
	def __init__( self, name = None, attrs = {}, data = None ):
		self.name = name
		self.attrs = attrs
		self.data = data

	def __nonzero__( self ):
		return self.name != None

class TextToken( Token ):
	def __init__( self, text = '' ):
		Token.__init__( self, name = '<empty>', data = text )

	def __str__( self ):
		return self.data

class TemplateToken( Token ):
	def __init__( self, name, attrs = {} ):
		Token.__init__( self, name, attrs )

	def __str__( self ):
		attrs = ''
		for key, value in self.attrs.items():
			attrs += '%s="%s" ' % ( key, value )
		return '<@%s %s@>' % ( self.name, attrs[ : -1 ] )

class IContextToken( TemplateToken, list ):
	def __init__( self, name, attrs, closing ):
		TemplateToken.__init__( self, name, attrs )
		list.__init__( self )
		self.closing = closing
		self.objects = []

	def clear( self ):
		while self.__len__():
			self.pop()

	def __str__( self ):
		content = ''
		for item in self:
			content += str( item )
		return TemplateToken.__str__( self ) + content + '<@/%s@>' % self.name

class ResolveToken( IContextToken ):
	def __init__( self, attrs = {}, closing = False ):
		IContextToken.__init__( self, 'resolve', attrs, closing )

class QueryToken( IContextToken, list ):
	def __init__( self, attrs = {}, closing = False ):
		IContextToken.__init__( self, 'query', attrs, closing )

class AttributeToken( TemplateToken ):
	def __init__( self, attrs = {}, value = '' ):
		TemplateToken.__init__( self, 'attribute', attrs )
		self.value = value

class PolicyToken( TemplateToken ):
	def __init__( self, attrs = {}, value = '' ):
		TemplateToken.__init__( self, 'policy', attrs )
		self.value = value
