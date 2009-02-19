#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  wizard table for UMCP dialogs
#
# Copyright (C) 2006-2009 Univention GmbH
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

import base

class Wizard( base.Element ):
	def __init__( self, title = '' ):
		base.Element.__init__( self )
		self._title = title
		self._content = base.List()
		self._image = None

	def set_image( self, image ):
		self._image = image

	def add_option( self, text, option ):
		self._content.add_row( [ option, text ] )

	def add_buttons( self, *args ):
		self._content.add_row( [ base.Fill( 2 ) ] )
		self._content.add_row( [ '', args ] )

	def setup( self ):
		self._image[ 'width' ] = '100'
		return base.Frame( [ base.List( content = [ [ self._image, self._content ] ] ) ], self._title )

WizardTypes = ( type( Wizard() ), )
