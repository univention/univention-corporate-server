# -*- coding: utf-8 -*-
#
# Univention Directory Reports
#  write an interpreted token structure to a file
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

import ConfigParser
import shlex

class Config( ConfigParser.ConfigParser ):
	def __init__( self, filename = '/etc/univention/directory/reports/config.ini' ):
		ConfigParser.ConfigParser.__init__( self )
		self._filename = filename
		self.read( filename )
		defaults = self.defaults()
		self._header = defaults.get( 'header', None )
		self._footer = defaults.get( 'footer', None )
		self.default_report_name = defaults.get( 'report', None )
		self._reports = {}

		for key, value in self.items( 'reports' ):
			try:
				module, name, filename = shlex.split( value )
			except:
				continue
			if self._reports.has_key( module ):
				self._reports[ module ].append( ( name, filename ) )
			else:
				self._reports[ module ] = [ ( name, filename ) ]

	def get_header( self ):
		return self._header

	def get_footer( self ):
		return self._footer

	def get_report_names( self, module ):
		reports = self._reports.get( module, [] )
		return [ item[ 0 ] for item in reports ]

	def get_report( self, module, name = None ):
		reports = self._reports.get( module, None )
		if not reports:
			return None
		if not name:
			# return filename of first report
			return reports[ 0 ][ 1 ]
		for text, filename in reports:
			if text == name:
				return filename

		return None
