# -*- coding: utf-8 -*-
#
# Univention Directory Reports
#  	creates a report document
#
# Copyright 2007-2014 Univention GmbH
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

import sys
import codecs
import os
import tempfile

from parser import *
from output import *
from interpreter import *
import admin
import subprocess

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
				raise NameError( "error: required file '%s' does not exist or is not readable" % \
								 filename )

	def __create_tempfile( self ):
		if self._type == Document.TYPE_LATEX:
			suffix = '.src'
		elif self._type == Document.TYPE_CSV:
			suffix = '.csv'
		else:
			suffix = self._template.rsplit('.', 1)[1]
		fd, filename = tempfile.mkstemp(suffix, 'univention-directory-reports-')
		os.chmod( filename, 0644 )
		os.close(fd)

		return filename

	def __append_file( self, fd, filename ):
		tmpfd = open( filename, 'r' )
		fd.write( tmpfd.read() )
		tmpfd.close()

	def create_source( self, objects = [] ):
		"""Create report from objects (list of DNs)."""
		tmpfile = self.__create_tempfile()
		admin.set_format( self._type == Document.TYPE_LATEX )
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
			if obj is None:
				print >>sys.stderr, "warning: dn '%s' not found, skipped." % dn
				continue
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
		"""Run pdflatex on latex_file and return path to generated file or None on errors."""
		cmd = ['/usr/bin/pdflatex', '-interaction=nonstopmode', '-halt-on-error', '-output-directory=%s' % os.path.dirname(latex_file), latex_file]
		devnull = open(os.path.devnull, 'w')
		try:
			env_vars = {'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin', 'HOME':'/var/cache/univention-directory-reports'}
			if not subprocess.call(cmd, stdout=devnull, stderr=devnull, env=env_vars):
				if not subprocess.call(cmd, stdout=devnull, stderr=devnull, env=env_vars):
					return '%s.pdf' % latex_file.rsplit('.', 1)[0]
			print >>sys.stderr, "error: failed to create PDF file"
			return None
		finally:
			devnull.close()
