#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  wizard table for UMCP dialogs
#
# Copyright 2006-2010 Univention GmbH
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

import base

class Wizard( base.Element ):
	def __init__( self, title = '' ):
		base.Element.__init__( self )
		self._title = title
		self._content = base.List( attributes = { 'width' : '100%' } )
		self._image = None

	def set_image( self, image ):
		self._image = image

	def add_option( self, text, option ):
		self._content.add_row( [ option, text ] )

	def add_buttons( self, *args ):
		if self._image:
			self._content.add_row( [ base.Fill( 2 ) ] )
			self._content.add_row( [ '', args ] )
		else:
			self._content.add_row( [ '' ] )
			self._content.add_row( [ args ] )

	def setup( self ):
		if self._image:
			self._image[ 'width' ] = '100'
			return base.Frame( [ base.List( content = [ [ base.Cell( self._image, { 'valign' : 'top' } ), self._content ] ], attributes = { 'width' : '100%' } ) ], self._title )
		else:
			return base.Section( self._title, self._content, attributes = { 'width' : '100%' } )

WizardTypes = ( type( Wizard() ), )
