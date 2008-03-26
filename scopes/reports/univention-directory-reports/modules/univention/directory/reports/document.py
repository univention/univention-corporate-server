# -*- coding: utf-8 -*-
#
# Univention Directory Reports
#  	creates a report document
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

import base64
import codecs
import os

from parser import *
from output import *
from interpreter import *
import admin

class Document( object ):
	( TYPE_LATEX, TYPE_CSV, TYPE_UNKNOWN ) = range( 3 )

	def __init__( self, template, header = None, footer = None ):
		self._template = template
		self._header = header
		self._footer = footer
		if self._template.endswith( '.tex' ):
			self._type = Document.TYPE_LATEX
		elif self._template.endswith( '.csv' ):
			self._type = Document.TYPE_CSV
		else:
			self._type = Document.TYPE_UNKNOWN
		self.__check_files()

	def __check_files( self ):
		if self._type == Document.TYPE_LATEX:
			files = ( self._header, self._footer, self._template )
		elif self._type == Document.TYPE_CSV:
			files = ( self._template, )
		else:
			files = tuple()
		for filename in files:
			if not os.path.isfile( filename ):
				raise Exception( "error: required file '%s' does not exist or is not readable" % \
								 filename )

	def __create_tempfile( self ):
		umask = os.umask( 0077 )
		unique = base64.encodestring( os.urandom( 12 ) )[ : -1 ]
		unique = unique.replace( '/', '-' )
		filename = os.path.join( '/tmp', 'univention-directory-reports-%d-%s.src' % ( os.getpid(), unique ) )
		fd = open( filename, 'w' )
		fd.close()
		os.umask( umask )

		return filename

	def __append_file( self, fd, filename ):
		tmpfd = open( filename, 'r' )
		fd.write( tmpfd.read() )
		tmpfd.close()

	def create_source( self, objects = [] ):
		tmpfile = self.__create_tempfile()
		parser = Parser( filename = self._template )
		parser.tokenize()
		tokens = parser._tokens
		fd = codecs.open( tmpfile, 'wb+', encoding = 'utf8' )
		if parser._header:
			fd.write( parser._header.data )
		elif self._header:
			self.__append_file( fd, self._header )

		for dn in objects:
			if isinstance( dn, basestring ):
				obj = admin.get_object( None, dn )
			else:
				obj = admin.cache_object( dn )
			tks = copy.deepcopy( tokens )
			interpret = Interpreter( obj, tks )
			interpret.run()
			output = Output( tks, fd = fd )
			output.write()
		if parser._footer:
			fd.write( parser._footer.data )
		elif self._footer:
			self.__append_file( fd, self._footer )
		fd.close()

		return tmpfile

	def create_pdf( self, latex_file ):
		cmd = 'pdflatex -interaction=nonstopmode -halt-on-error -output-directory=%s %s' % \
			  ( os.path.dirname( latex_file ), latex_file )
		if not os.system( '%s &> /dev/null' % cmd ):
			if not os.system( '%s &> /dev/null' % cmd ):
				return latex_file[ : -4 ] + '.pdf'
			else:
				print >>sys.stderr, "error: failed to create PDF file"
		else:
			print >>sys.stderr, "error: failed to create PDF file"

		return None
