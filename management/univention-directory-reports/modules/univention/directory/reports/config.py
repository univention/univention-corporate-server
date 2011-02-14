# -*- coding: utf-8 -*-
#
# Univention Directory Reports
#  write an interpreted token structure to a file
#
# Copyright 2007-2010 Univention GmbH
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

import ConfigParser
import shlex

class Config( ConfigParser.ConfigParser ):
	def __init__( self, filename = '/etc/univention/directory/reports/config.ini' ):
		ConfigParser.ConfigParser.__init__( self )
		self._filename = filename
		self.read( filename )
		defaults = self.defaults()
		self.default_report_name = defaults.get( 'report', None )
		self._reports = {}
		
		# get the language, defaults to English if nothing is set
		if not self._lang:
			self._lang = "en_US"

		for key, value in self.items( 'reports' ):
			try:
				module, name, dir, filename = shlex.split( value )
			except:
				continue
			if self._reports.has_key( module ):
				self._reports[ module ].append( ( name, dir, filename ) )
			else:
				self._reports[ module ] = [ ( name, dir, filename ) ]

	def _get_report_entry(self, module, name = None):
		"""Find the correct internal report entry for a given a module and a report name."""
		# return None for non-existent module
		if not self._reports.has_key( module ):
			return None
		# return first report if only the module name is given
		if not name:
			return self._reports[module][0]
		# if module name and report name are given, try to find the correct entry
		for report in self._reports[module]:
			if report[0] == name:
				return report
		# if anything fails, return None
		return None

	def get_header( self, module, name = None ):
		report = self._get_report_entry(module, name)
		if not report:
			return None
		return "%s/%s/header.tex" % (report[1], self._lang)

	def get_footer( self, module, name = None ):
		report = self._get_report_entry(module, name)
		if not report:
			return None
		return "%s/%s/footer.tex" % (report[1], self._lang)

	def get_report_names( self, module ):
		reports = self._reports.get( module, [] )
		return [ item[ 0 ] for item in reports ]

	def get_report( self, module, name = None ):
		report = self._get_report_entry(module, name)
		if not report:
			return None
		return "%s/%s/%s" % (report[1], self._lang, report[2])

